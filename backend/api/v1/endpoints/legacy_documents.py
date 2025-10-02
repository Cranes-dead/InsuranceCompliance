"""
LEGACY FILE - Migrated from old structure
Original location: legacy_documents.py
Migration date: 2025-09-26 23:55:40

[WARNING] This file needs manual review and integration with the new structure:
1. Update imports to use new package structure
2. Integrate with new service layer
3. Update configuration usage
4. Add proper error handling
5. Update tests

Remove this header once integration is complete.
"""


from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import uuid
from pathlib import Path
from datetime import datetime
import logging
from typing import List

from ..models.schemas import (
    DocumentUploadResponse, 
    DocumentInfo,
    DocumentType,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Configuration
UPLOAD_DIR = Path("./data/uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (this is approximate from headers)
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    return True

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for compliance analysis"""
    try:
        # Validate file
        validate_file(file)
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Create safe filename
        original_name = file.filename
        file_ext = Path(original_name).suffix
        safe_filename = f"{document_id}{file_ext}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Save file
        content = await file.read()
        
        # Check actual file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size {len(content)} exceeds maximum allowed size of {MAX_FILE_SIZE}"
            )
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # TODO: Save document metadata to database
        
        logger.info(f"Document uploaded: {document_id}, file: {original_name}")
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=original_name,
            file_size=len(content),
            status="uploaded",
            upload_timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during file upload")

@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document_info(document_id: str):
    """Get information about a specific document"""
    try:
        # TODO: Fetch from database
        # For now, check if file exists
        files = list(UPLOAD_DIR.glob(f"{document_id}.*"))
        if not files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = files[0]
        stat = file_path.stat()
        
        return DocumentInfo(
            document_id=document_id,
            filename=file_path.name,
            document_type=DocumentType.OTHER,  # TODO: Determine from content
            file_size=stat.st_size,
            upload_timestamp=datetime.fromtimestamp(stat.st_ctime),
            status="uploaded"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document info for {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[DocumentInfo])
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = []
        
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                document_id = file_path.stem
                stat = file_path.stat()
                
                documents.append(DocumentInfo(
                    document_id=document_id,
                    filename=file_path.name,
                    document_type=DocumentType.OTHER,
                    file_size=stat.st_size,
                    upload_timestamp=datetime.fromtimestamp(stat.st_ctime),
                    status="uploaded"
                ))
        
        return documents
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    try:
        files = list(UPLOAD_DIR.glob(f"{document_id}.*"))
        if not files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = files[0]
        file_path.unlink()
        
        # TODO: Remove from database
        
        logger.info(f"Document deleted: {document_id}")
        
        return {"message": f"Document {document_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")