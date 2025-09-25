from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
import logging
import asyncio
import uuid
from datetime import datetime
from pathlib import Path

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

# In-memory storage for batch jobs (in production, use Redis or database)
batch_jobs: Dict[str, Dict] = {}

# Simulated processing (replace with actual ML inference)
async def analyze_document(document_id: str, analysis_type: str = "full") -> ComplianceAnalysisResponse:
    """Analyze a single document for compliance"""
    try:
        # TODO: Load document from storage
        # TODO: Run through Legal BERT model
        # TODO: Generate explanations with Ollama
        # TODO: Extract violations and recommendations
        
        # Simulated processing time
        await asyncio.sleep(2)
        
        # Mock results for demonstration
        violations = [
            ViolationDetail(
                type="REGULATION_BREACH",
                description="Policy terms do not comply with IRDAI circular XYZ-2023",
                severity="HIGH",
                regulation_reference="IRDAI/REG/2023/001",
                suggested_fix="Update policy wording to align with regulatory requirements"
            )
        ]
        
        recommendations = [
            "Review and update policy terms to ensure IRDAI compliance",
            "Consult with legal team for regulatory interpretation",
            "Implement regular compliance audits"
        ]
        
        explanation = "This document has been classified as non-compliant due to several regulatory violations..."
        
        return ComplianceAnalysisResponse(
            document_id=document_id,
            classification=ComplianceClassification.NON_COMPLIANT,
            confidence=0.87,
            violations=violations,
            recommendations=recommendations,
            explanation=explanation,
            analysis_timestamp=datetime.utcnow(),
            processing_time=2.0
        )
        
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