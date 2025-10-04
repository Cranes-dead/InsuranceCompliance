"""
Policy management endpoints for Next.js frontend.
Handles policy upload, retrieval, and listing.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import shutil

from app.core import get_logger
from app.services.compliance_service import ComplianceService
from ...dependencies import get_compliance_service

logger = get_logger(__name__)

router = APIRouter()

# In-memory policy storage (use database in production)
policies_store: Dict[str, Dict[str, Any]] = {}


@router.post("/upload")
async def upload_policy(
    file: UploadFile = File(...),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """
    Upload a policy document and start analysis.
    
    Returns:
        Policy ID and initial status
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Generate policy ID
        policy_id = str(uuid4())
        
        # Save uploaded file
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{policy_id}.pdf"
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded policy {policy_id}: {file.filename}")
        
        # Start analysis
        try:
            result = await compliance_service.analyze_document(
                document_path=str(file_path),
                document_id=policy_id,
                analysis_type="full",
                include_explanation=True
            )
            
            # Store policy data
            policy_data = {
                "id": policy_id,
                "filename": file.filename,
                "classification": result.classification,
                "confidence": result.confidence,
                "compliance_score": result.metadata.get("compliance_score", 0),
                "violations": [
                    {
                        "severity": v.severity,
                        "type": v.type,
                        "description": v.description,
                        "regulation_reference": v.regulation_reference,
                        "recommendation": getattr(v, 'recommendation', getattr(v, 'suggested_action', ''))
                    }
                    for v in result.violations
                ],
                "recommendations": result.recommendations,
                "explanation": result.explanation,
                "rag_metadata": result.metadata,
                "created_at": datetime.utcnow().isoformat(),
                "uploaded_at": datetime.utcnow().isoformat(),
                "last_analyzed": datetime.utcnow().isoformat()
            }
            
            policies_store[policy_id] = policy_data
            
            return {
                "id": policy_id,
                "filename": file.filename,
                "status": "completed",
                "message": "Policy uploaded and analyzed successfully"
            }
            
        except Exception as e:
            logger.error(f"Analysis failed for {policy_id}: {e}")
            
            # Store with error status
            policy_data = {
                "id": policy_id,
                "filename": file.filename,
                "classification": "REQUIRES_REVIEW",
                "confidence": 0.0,
                "compliance_score": 0,
                "violations": [],
                "recommendations": ["Manual review required due to analysis error"],
                "explanation": f"Analysis encountered an error: {str(e)}",
                "rag_metadata": {
                    "regulations_retrieved": 0,
                    "top_sources": []
                },
                "created_at": datetime.utcnow().isoformat(),
                "uploaded_at": datetime.utcnow().isoformat(),
                "last_analyzed": datetime.utcnow().isoformat()
            }
            
            policies_store[policy_id] = policy_data
            
            return {
                "id": policy_id,
                "filename": file.filename,
                "status": "completed_with_errors",
                "message": "Policy uploaded but analysis had issues"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/policies/{policy_id}")
async def get_policy_analysis(policy_id: str):
    """
    Get analysis results for a specific policy.
    
    Args:
        policy_id: Policy UUID
        
    Returns:
        Complete policy analysis data
    """
    try:
        if policy_id not in policies_store:
            raise HTTPException(
                status_code=404,
                detail=f"Policy {policy_id} not found"
            )
        
        return policies_store[policy_id]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving policy {policy_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving policy: {str(e)}"
        )


@router.get("/policies")
async def get_all_policies():
    """
    Get list of all analyzed policies.
    
    Returns:
        List of policies with summary information
    """
    try:
        policies_list = [
            {
                "id": policy["id"],
                "filename": policy["filename"],
                "status": policy["classification"],
                "uploadedAt": policy["uploaded_at"],
                "lastAnalyzed": policy["last_analyzed"],
                "score": policy["compliance_score"]
            }
            for policy in policies_store.values()
        ]
        
        # Sort by upload date (newest first)
        policies_list.sort(key=lambda x: x["uploadedAt"], reverse=True)
        
        return policies_list
    
    except Exception as e:
        logger.error(f"Error retrieving policies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving policies: {str(e)}"
        )


@router.get("/statistics")
async def get_statistics():
    """
    Get dashboard statistics.
    
    Returns:
        Statistics about all policies
    """
    try:
        total_policies = len(policies_store)
        
        if total_policies == 0:
            return {
                "totalPolicies": 0,
                "compliantPolicies": 0,
                "nonCompliantPolicies": 0,
                "reviewRequired": 0,
                "averageScore": 0,
                "recentAnalyses": []
            }
        
        compliant = sum(
            1 for p in policies_store.values()
            if p["classification"] == "COMPLIANT"
        )
        
        non_compliant = sum(
            1 for p in policies_store.values()
            if p["classification"] == "NON_COMPLIANT"
        )
        
        review_required = sum(
            1 for p in policies_store.values()
            if p["classification"] == "REQUIRES_REVIEW"
        )
        
        total_score = sum(p["compliance_score"] for p in policies_store.values())
        average_score = int(total_score / total_policies) if total_policies > 0 else 0
        
        # Get recent analyses (last 5)
        recent = sorted(
            policies_store.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )[:5]
        
        return {
            "totalPolicies": total_policies,
            "compliantPolicies": compliant,
            "nonCompliantPolicies": non_compliant,
            "reviewRequired": review_required,
            "averageScore": average_score,
            "recentAnalyses": recent
        }
    
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating statistics: {str(e)}"
        )


@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str):
    """
    Delete a policy and its analysis.
    
    Args:
        policy_id: Policy UUID
    """
    try:
        if policy_id not in policies_store:
            raise HTTPException(
                status_code=404,
                detail=f"Policy {policy_id} not found"
            )
        
        # Delete file
        file_path = Path(f"data/uploads/{policy_id}.pdf")
        if file_path.exists():
            file_path.unlink()
        
        # Remove from store
        del policies_store[policy_id]
        
        logger.info(f"Deleted policy {policy_id}")
        
        return {
            "message": f"Policy {policy_id} deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting policy {policy_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting policy: {str(e)}"
        )
