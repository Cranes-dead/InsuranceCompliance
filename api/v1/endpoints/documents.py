"""
Document management API endpoints.
Next.js compatible file upload and document management.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from typing import List, Optional
import shutil
import os
from pathlib import Path
from uuid import uuid4

from app.core import get_logger, settings
from app.core.exceptions import FileValidationError, DocumentProcessingError
from app.models import (
    DocumentUploadResponse,
    DocumentInfo,
    DocumentType,
    ProcessingStatus,
    PaginationParams,
    PaginatedResponse
)
from app.services.document_service import DocumentService
from app.processing.parsers.document_parser import DocumentParser

logger = get_logger(__name__)

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.POLICY),
    metadata: Optional[str] = Form(None)  # JSON string for metadata
):
    """
    Upload a document for compliance analysis.
    
    Supports PDF, TXT, and DOCX files up to the configured size limit.
    Returns document ID for subsequent analysis requests.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Generate unique document ID
        document_id = str(uuid4())
        
        # Ensure upload directory exists
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        file_path = settings.UPLOAD_DIR / f"{document_id}{file_ext}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Validate file size
        if file_size > settings.MAX_FILE_SIZE:
            file_path.unlink()  # Delete the file
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size} bytes. Maximum: {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Parse metadata if provided
        import json
        parsed_metadata = {}
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                logger.warning("Invalid metadata JSON provided")
        
        response = DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            document_type=document_type,
            metadata=parsed_metadata
        )
        
        logger.info(f"Document uploaded successfully: {document_id} ({file.filename})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/", response_model=PaginatedResponse)
async def list_documents(
    page: int = 1,
    size: int = 20,
    document_type: Optional[DocumentType] = None,
    status: Optional[ProcessingStatus] = None
):
    """
    List uploaded documents with pagination and filtering.
    
    Supports filtering by document type and processing status.
    """
    try:
        # Basic file listing (in production, this would query a database)
        upload_dir = settings.UPLOAD_DIR
        if not upload_dir.exists():
            return PaginatedResponse(
                items=[],
                total=0,
                page=page,
                size=size,
                pages=0,
                has_next=False,
                has_previous=False
            )
        
        # Get all files
        all_files = list(upload_dir.glob("*"))
        
        # Apply filtering (basic implementation)
        filtered_files = []
        for file_path in all_files:
            if file_path.is_file():
                # Extract document ID from filename
                doc_id = file_path.stem
                
                doc_info = DocumentInfo(
                    document_id=doc_id,
                    filename=f"document{file_path.suffix}",
                    file_size=file_path.stat().st_size,
                    document_type=document_type or DocumentType.POLICY,
                    status=ProcessingStatus.COMPLETED,
                    upload_timestamp=datetime.fromtimestamp(file_path.stat().st_mtime)
                )
                
                # Apply filters
                if document_type and doc_info.document_type != document_type:
                    continue
                if status and doc_info.status != status:
                    continue
                
                filtered_files.append(doc_info)
        
        # Pagination
        total = len(filtered_files)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        page_items = filtered_files[start_idx:end_idx]
        
        pages = (total + size - 1) // size  # Ceiling division
        
        return PaginatedResponse(
            items=[item.dict() for item in page_items],
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=page < pages,
            has_previous=page > 1
        )
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document_info(document_id: str):
    """
    Get information about a specific document.
    
    Returns document metadata and processing status.
    """
    try:
        # Find document file
        upload_dir = settings.UPLOAD_DIR
        doc_files = list(upload_dir.glob(f"{document_id}.*"))
        
        if not doc_files:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        doc_file = doc_files[0]
        doc_info = DocumentInfo(
            document_id=document_id,
            filename=f"document{doc_file.suffix}",
            file_size=doc_file.stat().st_size,
            document_type=DocumentType.POLICY,  # Default
            status=ProcessingStatus.COMPLETED,
            upload_timestamp=datetime.fromtimestamp(doc_file.stat().st_mtime),
            last_modified=datetime.fromtimestamp(doc_file.stat().st_mtime)
        )
        
        return doc_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document info: {str(e)}"
        )


@router.get("/{document_id}/download")
async def download_document(document_id: str):
    """
    Download a document file.
    
    Returns the original uploaded file for download.
    """
    try:
        # Find document file
        upload_dir = settings.UPLOAD_DIR
        doc_files = list(upload_dir.glob(f"{document_id}.*"))
        
        if not doc_files:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        doc_file = doc_files[0]
        
        return FileResponse(
            path=str(doc_file),
            filename=f"document_{document_id}{doc_file.suffix}",
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and its associated data.
    
    Removes the document file and any cached analysis results.
    """
    try:
        # Find and delete document file
        upload_dir = settings.UPLOAD_DIR
        doc_files = list(upload_dir.glob(f"{document_id}.*"))
        
        if not doc_files:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        # Delete file
        for doc_file in doc_files:
            doc_file.unlink()
        
        logger.info(f"Document deleted successfully: {document_id}")
        return {"message": f"Document {document_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/{document_id}/validate")
async def validate_document(document_id: str):
    """
    Validate a document for compliance analysis readiness.
    
    Checks document format, size, and content accessibility.
    """
    try:
        # Find document file
        upload_dir = settings.UPLOAD_DIR
        doc_files = list(upload_dir.glob(f"{document_id}.*"))
        
        if not doc_files:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        doc_file = doc_files[0]
        
        # Use document parser for validation
        parser = DocumentParser()
        validation_result = await parser.validate_document(
            str(doc_file),
            max_size=settings.MAX_FILE_SIZE
        )
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )