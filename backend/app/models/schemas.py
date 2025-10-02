"""
Pydantic schemas for API requests and responses.
Next.js friendly with proper JSON serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID, uuid4

from .enums import (
    ComplianceClassification,
    DocumentType,
    AnalysisType,
    ProcessingStatus,
    BatchStatus,
    ViolationType,
    ViolationSeverity
)


# Base Schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        # JSON serialization for Next.js compatibility
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
        # Allow using enums by value
        use_enum_values = True
        # Validate field defaults
        validate_all = True


# Document Schemas
class DocumentUploadRequest(BaseSchema):
    """Schema for document upload request."""
    document_type: DocumentType = DocumentType.POLICY
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentUploadResponse(BaseSchema):
    """Schema for document upload response."""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    document_type: DocumentType
    status: ProcessingStatus = ProcessingStatus.PENDING
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentInfo(BaseSchema):
    """Schema for document information."""
    document_id: str
    filename: str
    file_size: int
    document_type: DocumentType
    status: ProcessingStatus
    upload_timestamp: datetime
    last_modified: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Analysis Schemas
class ComplianceAnalysisRequest(BaseSchema):
    """Schema for compliance analysis request."""
    document_id: str = Field(..., description="Document ID to analyze")
    analysis_type: AnalysisType = Field(
        AnalysisType.FULL, 
        description="Type of analysis to perform"
    )
    include_explanation: bool = Field(
        True, 
        description="Whether to include AI-generated explanations"
    )
    custom_rules: Optional[List[str]] = Field(
        None,
        description="Custom rules to apply during analysis"
    )


class ViolationDetail(BaseSchema):
    """Schema for compliance violation details."""
    violation_id: str = Field(default_factory=lambda: str(uuid4()))
    type: ViolationType
    severity: ViolationSeverity
    description: str = Field(..., description="Human-readable violation description")
    regulation_reference: Optional[str] = Field(
        None,
        description="Reference to specific regulation"
    )
    suggested_action: Optional[str] = Field(
        None,
        description="Recommended action to resolve violation"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence score for this violation"
    )
    location: Optional[Dict[str, Any]] = Field(
        None,
        description="Location information within document"
    )


class ComplianceAnalysisResponse(BaseSchema):
    """Schema for compliance analysis response."""
    analysis_id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    classification: ComplianceClassification
    confidence: float = Field(..., ge=0.0, le=1.0)
    violations: List[ViolationDetail] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    explanation: Optional[str] = Field(
        None,
        description="AI-generated explanation of the analysis"
    )
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time: Optional[float] = Field(
        None,
        description="Analysis processing time in seconds"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Batch Analysis Schemas
class BatchAnalysisRequest(BaseSchema):
    """Schema for batch analysis request."""
    document_ids: List[str] = Field(
        ..., 
        description="List of document IDs to analyze"
    )
    analysis_type: AnalysisType = AnalysisType.FULL
    include_explanation: bool = True
    custom_rules: Optional[List[str]] = None
    priority: Optional[str] = Field("normal", description="Batch processing priority")
    
    @validator("document_ids")
    def validate_unique_documents(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Document IDs must be unique")
        return v


class BatchAnalysisResponse(BaseSchema):
    """Schema for batch analysis response."""
    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    status: BatchStatus = BatchStatus.CREATED
    total_documents: int
    completed_documents: int = 0
    failed_documents: int = 0
    created_timestamp: datetime = Field(default_factory=datetime.utcnow)
    started_timestamp: Optional[datetime] = None
    completed_timestamp: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0)
    results: List[ComplianceAnalysisResponse] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class BatchStatusResponse(BaseSchema):
    """Schema for batch status response."""
    batch_id: str
    status: BatchStatus
    total_documents: int
    completed_documents: int
    failed_documents: int
    progress_percentage: float
    estimated_completion: Optional[datetime] = None
    created_timestamp: datetime
    started_timestamp: Optional[datetime] = None
    completed_timestamp: Optional[datetime] = None


# Health Check Schemas
class HealthCheckResponse(BaseSchema):
    """Schema for health check response."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    services: Dict[str, str] = Field(default_factory=dict)
    uptime: Optional[float] = None


# Error Schemas
class ErrorDetail(BaseSchema):
    """Schema for error details."""
    error_code: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseSchema):
    """Schema for error responses."""
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# Pagination Schemas
class PaginationParams(BaseSchema):
    """Schema for pagination parameters."""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("desc")


class PaginatedResponse(BaseSchema):
    """Generic paginated response schema."""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_previous: bool


# Statistics Schemas
class ComplianceStats(BaseSchema):
    """Schema for compliance statistics."""
    total_documents: int
    compliant_count: int
    non_compliant_count: int
    requires_review_count: int
    compliance_rate: float = Field(..., ge=0.0, le=100.0)
    average_confidence: float = Field(..., ge=0.0, le=1.0)
    most_common_violations: List[Dict[str, Union[str, int]]]
    analysis_trends: Dict[str, Any] = Field(default_factory=dict)