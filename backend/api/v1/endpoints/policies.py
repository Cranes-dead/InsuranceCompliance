"""
Policy management endpoints with Supabase database integration.
Handles policy upload, retrieval, and listing with comprehensive validation.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import shutil

from app.core import get_logger
from app.core.config import settings
from app.services.compliance_service import ComplianceService
from app.db import get_supabase_service
from ...dependencies import get_compliance_service

logger = get_logger(__name__)

router = APIRouter()

# File validation constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MIN_FILE_SIZE = 100  # 100 bytes
ALLOWED_EXTENSIONS = [".pdf"]


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded file for size and format.
    
    Returns:
        (is_valid, error_message)
    """
    # Check filename exists
    if not file.filename:
        return False, "Filename is missing"
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Only PDF files are supported. Got: {file_ext}"
    
    # Check file size (if available from browser)
    if hasattr(file, 'size') and file.size:
        if file.size > MAX_FILE_SIZE:
            size_mb = file.size / (1024 * 1024)
            return False, f"File size ({size_mb:.1f}MB) exceeds maximum allowed size of 50MB"
        if file.size < MIN_FILE_SIZE:
            return False, "File is too small or empty"
    
    return True, ""


def verify_file_integrity(file_path: Path) -> tuple[bool, str, int]:
    """Verify file was written correctly and get file size.
    
    Returns:
        (is_valid, error_message, file_size_bytes)
    """
    try:
        if not file_path.exists():
            return False, "File was not saved correctly", 0
        
        file_size = file_path.stat().st_size
        
        if file_size < MIN_FILE_SIZE:
            return False, "File is empty or corrupted", file_size
        
        if file_size > MAX_FILE_SIZE:
            return False, f"File size exceeds maximum ({MAX_FILE_SIZE} bytes)", file_size
        
        # Verify file can be opened
        with file_path.open('rb') as f:
            # Read first few bytes to verify file is readable
            header = f.read(4)
            if not header:
                return False, "File is empty", file_size
            
            # Check PDF magic number
            if header[:4] != b'%PDF':
                return False, "File does not appear to be a valid PDF", file_size
        
        return True, "", file_size
        
    except Exception as e:
        return False, f"File integrity check failed: {str(e)}", 0


@router.post("/upload")
async def upload_policy(
    file: UploadFile = File(...),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """
    Upload a policy document and start analysis with comprehensive validation.
    
    Edge cases handled:
    - File size validation (min/max)
    - File format validation (PDF only)
    - File integrity check after upload
    - Database persistence
    - Analysis error handling
    
    Returns:
        Policy ID and status
    """
    db = get_supabase_service()
    
    try:
        # Validate file before processing
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Generate policy ID
        policy_id = str(uuid4())
        
        # Save uploaded file using absolute path from settings
        upload_dir = settings.UPLOAD_DIR
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{policy_id}.pdf"
        
        # Write file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Verify file integrity after write
        is_valid, error_msg, file_size = verify_file_integrity(file_path)
        if not is_valid:
            file_path.unlink(missing_ok=True)  # Delete corrupted file
            raise HTTPException(status_code=400, detail=error_msg)
        
        logger.info(f"✅ Uploaded policy {policy_id}: {file.filename} ({file_size} bytes)")
        
        # Start analysis
        try:
            result = await compliance_service.analyze_document(
                document_path=str(file_path),
                document_id=policy_id,
                analysis_type="full",
                include_explanation=True
            )
            
            # Prepare policy data for database
            policy_data = {
                "id": policy_id,
                "filename": file.filename,
                "classification": str(result.classification.value if hasattr(result.classification, 'value') else result.classification),
                "confidence": float(result.confidence),
                "compliance_score": int(result.metadata.get("compliance_score", 0)),
                "violations": [
                    {
                        "severity": str(v.severity),
                        "type": str(v.type),
                        "description": v.description,
                        "regulation_reference": v.regulation_reference,
                        "recommendation": getattr(v, 'recommendation', getattr(v, 'suggested_action', ''))
                    }
                    for v in result.violations
                ],
                "recommendations": result.recommendations,
                "explanation": result.explanation or "",
                "rag_metadata": result.metadata or {},
                "file_path": str(file_path),
                "file_size_bytes": file_size,
            }
            
            # Store in database
            await db.create_policy(policy_data)
            
            return {
                "id": policy_id,
                "filename": file.filename,
                "status": "completed",
                "message": "Policy uploaded and analyzed successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis failed for {policy_id}: {e}")
            
            # Store with error status in database
            error_policy_data = {
                "id": policy_id,
                "filename": file.filename,
                "classification": "REQUIRES_REVIEW",
                "confidence": 0.0,
                "compliance_score": 0,
                "violations": [],
                "recommendations": ["Manual review required due to analysis error"],
                "explanation": "Analysis encountered an error. Please try uploading again or contact support.",
                "rag_metadata": {"error": str(e)},
                "file_path": str(file_path),
                "file_size_bytes": file_size,
            }
            
            await db.create_policy(error_policy_data)
            
            return {
                "id": policy_id,
                "filename": file.filename,
                "status": "completed_with_errors",
                "message": "Policy uploaded but analysis had issues"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Upload failed. Please try again."
        )


@router.get("/policies/{policy_id}")
async def get_policy_analysis(policy_id: str):
    """
    Get analysis results for a specific policy from database.
    
    Args:
        policy_id: Policy UUID
        
    Returns:
        Complete policy analysis data
    """
    db = get_supabase_service()
    
    try:
        policy = await db.get_policy(policy_id)
        
        if not policy:
            raise HTTPException(
                status_code=404,
                detail=f"Policy {policy_id} not found"
            )
        
        return policy
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving policy {policy_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving policy"
        )


@router.get("/policies")
async def get_all_policies():
    """
    Get list of all analyzed policies from database.
    
    Returns:
        List of policies with summary information
    """
    db = get_supabase_service()
    
    try:
        policies = await db.get_all_policies()
        
        # Format for frontend with safe column access
        policies_list = [
            {
                "id": policy.get("id", ""),
                "filename": policy.get("filename", "Unknown"),
                "status": policy.get("classification", "REQUIRES_REVIEW"),
                "uploadedAt": policy.get("uploaded_at", policy.get("created_at", None)),
                "lastAnalyzed": policy.get("last_analyzed_at", policy.get("updated_at", None)),
                "score": policy.get("compliance_score", 0)
            }
            for policy in policies
        ]
        
        return policies_list
    
    except Exception as e:
        logger.error(f"❌ Error retrieving policies: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving policies"
        )


@router.get("/statistics")
async def get_statistics():
    """
    Get dashboard statistics from database.
    
    Returns:
        Statistics about all policies
    """
    db = get_supabase_service()
    
    try:
        stats = await db.get_statistics()
        return stats
    
    except Exception as e:
        logger.error(f"❌ Error retrieving statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving statistics"
        )


@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str):
    """
    Delete a policy and its associated chat history.
    
    Args:
        policy_id: Policy UUID
        
    Returns:
        Success message
    """
    db = get_supabase_service()
    
    try:
        # Get policy to find file path
        policy = await db.get_policy(policy_id)
        
        if not policy:
            raise HTTPException(
                status_code=404,
                detail=f"Policy {policy_id} not found"
            )
        
        # Delete from database (cascades to chat)
        await db.delete_policy(policy_id)
        
        # Delete file from disk
        try:
            file_path = Path(policy["file_path"])
            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️  Deleted file: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️  Could not delete file: {e}")
        
        return {
            "message": f"Policy {policy_id} deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting policy {policy_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error deleting policy"
        )
