"""
Compliance analysis API endpoints.
Next.js compatible endpoints with proper async handling.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from typing import Dict, List
import asyncio
from datetime import datetime
from uuid import uuid4

from app.core import get_logger
from app.models import (
    ComplianceAnalysisRequest,
    ComplianceAnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BatchStatusResponse
)
from app.services.compliance_service import ComplianceService
from ...dependencies import get_compliance_service

logger = get_logger(__name__)

router = APIRouter()

# In-memory batch status tracking (use Redis in production)
# Bounded to prevent unbounded memory growth
MAX_BATCH_STORE_SIZE = 1000
batch_status_store: Dict[str, dict] = {}


def _store_batch_status(batch_id: str, data: dict) -> None:
    """Store batch status with automatic eviction of old completed entries."""
    if len(batch_status_store) >= MAX_BATCH_STORE_SIZE:
        # Evict oldest completed/failed batches first
        completed_ids = [
            bid for bid, bdata in batch_status_store.items()
            if bdata.get("status") in ("completed", "failed", "cancelled")
        ]
        # Sort by created_at and remove oldest half
        completed_ids.sort(
            key=lambda bid: batch_status_store[bid].get("created_at", ""),
        )
        for bid in completed_ids[:len(completed_ids) // 2 + 1]:
            del batch_status_store[bid]
        
        if len(batch_status_store) >= MAX_BATCH_STORE_SIZE:
            # Still full — evict oldest regardless of status
            oldest_id = min(
                batch_status_store,
                key=lambda bid: batch_status_store[bid].get("created_at", "")
            )
            del batch_status_store[oldest_id]
        
        logger.warning(
            f"Batch store evicted old entries (was {MAX_BATCH_STORE_SIZE}). "
            "Consider using Redis for production batch tracking."
        )
    
    batch_status_store[batch_id] = data


@router.post("/analyze", response_model=ComplianceAnalysisResponse)
async def analyze_document(
    request: ComplianceAnalysisRequest,
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """
    Analyze a single document for compliance violations.
    
    This endpoint performs real-time compliance analysis and returns
    detailed results including violations and recommendations.
    """
    try:
        # For demo purposes, we'll use a mock document path
        # In production, this would retrieve the actual document
        document_path = f"./data/uploads/{request.document_id}.pdf"
        
        result = await compliance_service.analyze_document(
            document_path=document_path,
            document_id=request.document_id,
            analysis_type=request.analysis_type,
            include_explanation=request.include_explanation,
            custom_rules=request.custom_rules
        )
        
        logger.info(f"Analysis completed for document {request.document_id}")
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed for document {request.document_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/batch", response_model=BatchAnalysisResponse)
async def start_batch_analysis(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """
    Start batch analysis of multiple documents.
    
    This endpoint initiates batch processing in the background
    and returns a batch ID for tracking progress.
    """
    try:
        batch_id = str(uuid4())
        
        # Initialize batch status
        batch_status = {
            "batch_id": batch_id,
            "status": "created",
            "total_documents": len(request.document_ids),
            "completed_documents": 0,
            "failed_documents": 0,
            "results": [],
            "errors": [],
            "created_at": datetime.now().isoformat()
        }
        
        _store_batch_status(batch_id, batch_status)
        
        # Start background processing
        background_tasks.add_task(
            _process_batch_analysis,
            batch_id,
            request,
            compliance_service
        )
        
        response = BatchAnalysisResponse(
            batch_id=batch_id,
            total_documents=len(request.document_ids),
            progress_percentage=0.0
        )
        
        logger.info(f"Started batch analysis {batch_id} for {len(request.document_ids)} documents")
        return response
        
    except Exception as e:
        logger.error(f"Failed to start batch analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start batch analysis: {str(e)}"
        )


@router.get("/batch/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """
    Get the status of a batch analysis.
    
    Returns current progress and results for the specified batch.
    """
    if batch_id not in batch_status_store:
        raise HTTPException(
            status_code=404,
            detail=f"Batch {batch_id} not found"
        )
    
    batch_data = batch_status_store[batch_id]
    
    return BatchStatusResponse(
        batch_id=batch_id,
        status=batch_data["status"],
        total_documents=batch_data["total_documents"],
        completed_documents=batch_data["completed_documents"],
        failed_documents=batch_data["failed_documents"],
        progress_percentage=round(
            (batch_data["completed_documents"] / batch_data["total_documents"]) * 100, 1
        ) if batch_data["total_documents"] > 0 else 0,
        created_timestamp=batch_data.get("created_timestamp", datetime.now())
    )


@router.get("/batch/{batch_id}/results")
async def get_batch_results(batch_id: str):
    """
    Get the complete results of a batch analysis.
    
    Returns all analysis results for the specified batch.
    """
    if batch_id not in batch_status_store:
        raise HTTPException(
            status_code=404,
            detail=f"Batch {batch_id} not found"
        )
    
    batch_data = batch_status_store[batch_id]
    
    if batch_data["status"] not in ["completed", "failed", "partial"]:
        raise HTTPException(
            status_code=400,
            detail=f"Batch {batch_id} is still processing"
        )
    
    return {
        "batch_id": batch_id,
        "status": batch_data["status"],
        "results": batch_data["results"],
        "errors": batch_data["errors"],
        "summary": {
            "total_documents": batch_data["total_documents"],
            "completed_documents": batch_data["completed_documents"],
            "failed_documents": batch_data["failed_documents"]
        }
    }


@router.delete("/batch/{batch_id}")
async def cancel_batch_analysis(batch_id: str):
    """
    Cancel a running batch analysis.
    
    Stops processing and cleans up resources for the specified batch.
    """
    if batch_id not in batch_status_store:
        raise HTTPException(
            status_code=404,
            detail=f"Batch {batch_id} not found"
        )
    
    batch_data = batch_status_store[batch_id]
    
    if batch_data["status"] in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Batch {batch_id} has already finished"
        )
    
    # Mark as cancelled
    batch_data["status"] = "cancelled"
    logger.info(f"Batch analysis {batch_id} cancelled")
    
    return {"message": f"Batch {batch_id} cancelled successfully"}


# NOTE: Statistics endpoint has been removed from this router.
# Use GET /api/v1/statistics (in policies router) for real database-backed stats.



async def _process_batch_analysis(
    batch_id: str,
    request: BatchAnalysisRequest,
    compliance_service: ComplianceService
):
    """
    Background task to process batch analysis.
    
    Updates batch status as documents are processed.
    """
    try:
        batch_data = batch_status_store[batch_id]
        batch_data["status"] = "running"
        
        # Prepare documents for analysis
        documents = [
            {"id": doc_id, "path": f"./data/uploads/{doc_id}.pdf"}
            for doc_id in request.document_ids
        ]
        
        # Process batch
        results = await compliance_service.analyze_batch(
            documents=documents,
            analysis_type=request.analysis_type,
            include_explanation=request.include_explanation,
            custom_rules=request.custom_rules
        )
        
        # Update batch status
        batch_data["results"] = [result.dict() for result in results]
        batch_data["completed_documents"] = len(results)
        batch_data["failed_documents"] = len(request.document_ids) - len(results)
        batch_data["status"] = "completed"
        
        logger.info(f"Batch analysis {batch_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Batch analysis {batch_id} failed: {e}")
        batch_data = batch_status_store.get(batch_id, {})
        batch_data["status"] = "failed"
        batch_data["errors"] = [str(e)]