from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
import logging
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from updated_compliance_system import RuleBasedComplianceEngine
from src.processing.parsers.document_parser import parse_document

from ..models.schemas import (
    ComplianceAnalysisRequest,
    ComplianceAnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    ViolationDetail,
    ComplianceClassification
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize the rule-based compliance engine
try:
    compliance_engine = RuleBasedComplianceEngine()
    logger.info("Rule-based compliance engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize compliance engine: {e}")
    compliance_engine = None

# In-memory storage for batch jobs (in production, use Redis or database)
batch_jobs: Dict[str, Dict] = {}

# Updated document analysis using rule-based system
async def analyze_document(document_id: str, analysis_type: str = "full") -> ComplianceAnalysisResponse:
    """Analyze a single document for compliance using rule-based engine"""
    try:
        if not compliance_engine:
            raise HTTPException(status_code=503, detail="Compliance engine not available")
        
        # Load document from storage
        upload_dir = Path("./data/uploads")
        document_files = list(upload_dir.glob(f"{document_id}.*"))
        
        if not document_files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_path = document_files[0]
        
        # Parse document content
        try:
            document_text = parse_document(str(document_path))
        except Exception as e:
            logger.error(f"Failed to parse document {document_id}: {e}")
            raise HTTPException(status_code=422, detail="Failed to parse document")
        
        # Perform rule-based compliance analysis
        start_time = datetime.utcnow()
        analysis_result = compliance_engine.classify_policy_text(document_text)
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Convert analysis result to API response format
        classification = ComplianceClassification(analysis_result['classification'])
        
        # Convert violations to ViolationDetail objects
        violations = []
        for violation in analysis_result.get('violations', []):
            violations.append(ViolationDetail(
                type=violation.get('type', 'REGULATORY_VIOLATION'),
                description=violation.get('description', ''),
                severity=violation.get('severity', 'MEDIUM').upper(),
                regulation_reference="IRDAI Motor Insurance Regulations",
                suggested_fix=violation.get('description', '')
            ))
        
        # Add violations for failed mandatory requirements
        for req in analysis_result.get('mandatory_compliance', []):
            if not req.get('compliant', True):
                violations.append(ViolationDetail(
                    type="MANDATORY_REQUIREMENT_FAILURE",
                    description=f"Failed requirement: {req.get('rule', 'Unknown requirement')}",
                    severity="HIGH",
                    regulation_reference="IRDAI Motor Insurance Regulations / Motor Vehicle Act 1988",
                    suggested_fix=req.get('issue', 'Ensure compliance with mandatory requirement')
                ))
        
        # Generate detailed explanation
        explanation = f"""
        Policy Classification: {analysis_result['classification']}
        Compliance Score: {analysis_result['compliance_score']:.2f}
        
        Analysis Summary:
        - Classification determined using rule-based regulatory analysis
        - Regulatory rules classified by type (Mandatory, Optional, Procedural, etc.)
        - Policy checked against extracted regulatory requirements
        
        Mandatory Requirements Status:
        """
        
        for req in analysis_result.get('mandatory_compliance', []):
            status = "✅ PASSED" if req.get('compliant', False) else "❌ FAILED"
            explanation += f"\n        • {status}: {req.get('rule', 'Unknown requirement')}"
            if req.get('found_amount') and req.get('required_amount'):
                explanation += f" (Found: Rs {req['found_amount']/100000:.0f}L, Required: Rs {req['required_amount']/100000:.0f}L)"
        
        if analysis_result.get('violations'):
            explanation += f"\n\n        Regulatory Violations Detected: {len(analysis_result['violations'])}"
        
        return ComplianceAnalysisResponse(
            document_id=document_id,
            classification=classification,
            confidence=analysis_result['confidence'],
            violations=violations,
            recommendations=analysis_result.get('recommendations', []),
            explanation=explanation.strip(),
            analysis_timestamp=datetime.utcnow(),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/compliance", response_model=ComplianceAnalysisResponse)
async def analyze_compliance(request: ComplianceAnalysisRequest):
    """Analyze a document for compliance violations"""
    try:
        # Check if document exists
        upload_dir = Path("./data/uploads")
        document_files = list(upload_dir.glob(f"{request.document_id}.*"))
        
        if not document_files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Perform analysis
        result = await analyze_document(request.document_id, request.analysis_type)
        
        # TODO: Save results to database
        
        logger.info(f"Compliance analysis completed for document: {request.document_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in compliance analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")

@router.post("/batch", response_model=BatchAnalysisResponse)
async def start_batch_analysis(request: BatchAnalysisRequest, background_tasks: BackgroundTasks):
    """Start batch analysis of multiple documents"""
    try:
        batch_id = str(uuid.uuid4())
        
        # Initialize batch job
        batch_jobs[batch_id] = {
            "batch_id": batch_id,
            "total_documents": len(request.document_ids),
            "completed": 0,
            "status": "processing",
            "results": [],
            "summary": None,
            "started_at": datetime.utcnow(),
            "completed_at": None
        }
        
        # Start background processing
        background_tasks.add_task(
            process_batch_analysis,
            batch_id,
            request.document_ids,
            request.analysis_type,
            request.include_explanations
        )
        
        logger.info(f"Started batch analysis: {batch_id} for {len(request.document_ids)} documents")
        
        return BatchAnalysisResponse(**batch_jobs[batch_id])
        
    except Exception as e:
        logger.error(f"Error starting batch analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to start batch analysis")

@router.get("/batch/{batch_id}", response_model=BatchAnalysisResponse)
async def get_batch_status(batch_id: str):
    """Get status of batch analysis"""
    if batch_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    return BatchAnalysisResponse(**batch_jobs[batch_id])

async def process_batch_analysis(batch_id: str, document_ids: List[str], 
                               analysis_type: str, include_explanations: bool):
    """Background task to process batch analysis"""
    try:
        results = []
        
        for document_id in document_ids:
            try:
                # Analyze document
                result = await analyze_document(document_id, analysis_type)
                results.append(result)
                
                # Update progress
                batch_jobs[batch_id]["completed"] += 1
                batch_jobs[batch_id]["results"] = results
                
                logger.info(f"Batch {batch_id}: Completed {len(results)}/{len(document_ids)} documents")
                
            except Exception as e:
                logger.error(f"Error processing document {document_id} in batch {batch_id}: {e}")
                continue
        
        # Generate summary
        summary = generate_batch_summary(results)
        
        # Update batch job
        batch_jobs[batch_id].update({
            "status": "completed",
            "results": results,
            "summary": summary,
            "completed_at": datetime.utcnow()
        })
        
        logger.info(f"Batch analysis completed: {batch_id}")
        
    except Exception as e:
        logger.error(f"Error in batch processing {batch_id}: {e}")
        batch_jobs[batch_id]["status"] = "failed"

def generate_batch_summary(results: List[ComplianceAnalysisResponse]) -> str:
    """Generate summary for batch analysis results"""
    if not results:
        return "No results to summarize"
    
    total = len(results)
    compliant = sum(1 for r in results if r.classification == ComplianceClassification.COMPLIANT)
    non_compliant = sum(1 for r in results if r.classification == ComplianceClassification.NON_COMPLIANT)
    needs_review = sum(1 for r in results if r.classification == ComplianceClassification.REQUIRES_REVIEW)
    
    avg_confidence = sum(r.confidence for r in results) / total
    
    summary = f"""
    Batch Analysis Summary:
    - Total Documents: {total}
    - Compliant: {compliant} ({compliant/total*100:.1f}%)
    - Non-Compliant: {non_compliant} ({non_compliant/total*100:.1f}%)
    - Requires Review: {needs_review} ({needs_review/total*100:.1f}%)
    - Average Confidence: {avg_confidence:.2f}
    
    Key Findings:
    - {non_compliant} documents require immediate attention
    - {needs_review} documents need manual review
    - Overall compliance rate: {compliant/total*100:.1f}%
    """
    
    return summary.strip()

@router.get("/results/{document_id}", response_model=ComplianceAnalysisResponse)
async def get_analysis_results(document_id: str):
    """Get stored analysis results for a document"""
    try:
        # TODO: Fetch from database
        # For now, return mock data
        raise HTTPException(status_code=404, detail="Analysis results not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching results for {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")