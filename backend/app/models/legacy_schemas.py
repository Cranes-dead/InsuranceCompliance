"""
LEGACY FILE - Migrated from old structure
Original location: legacy_schemas.py
Migration date: 2025-09-26 23:55:40

[WARNING] This file needs manual review and integration with the new structure:
1. Update imports to use new package structure
2. Integrate with new service layer
3. Update configuration usage
4. Add proper error handling
5. Update tests

Remove this header once integration is complete.
"""


from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ComplianceClassification(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"

class DocumentType(str, Enum):
    POLICY = "policy"
    CLAIM = "claim"
    GUIDELINE = "guideline"
    OTHER = "other"

# Request Models
class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    status: str
    upload_timestamp: datetime

class ComplianceAnalysisRequest(BaseModel):
    document_id: str
    analysis_type: str = Field(default="full", description="Type of analysis: 'full', 'quick', or 'specific'")
    include_explanation: bool = Field(default=True, description="Whether to include AI-generated explanations")

class BatchAnalysisRequest(BaseModel):
    document_ids: List[str]
    analysis_type: str = Field(default="full", description="Type of analysis for all documents")
    include_explanations: bool = Field(default=True, description="Whether to include explanations for all")

class ComplianceQueryRequest(BaseModel):
    question: str
    context: Optional[str] = Field(None, description="Additional context for the question")

# Response Models
class ViolationDetail(BaseModel):
    type: str
    description: str
    severity: str = Field(description="HIGH, MEDIUM, LOW")
    regulation_reference: Optional[str] = None
    suggested_fix: Optional[str] = None

class ComplianceAnalysisResponse(BaseModel):
    document_id: str
    classification: ComplianceClassification
    confidence: float = Field(ge=0.0, le=1.0)
    violations: List[ViolationDetail] = []
    recommendations: List[str] = []
    explanation: Optional[str] = None
    analysis_timestamp: datetime
    processing_time: float = Field(description="Processing time in seconds")

class BatchAnalysisResponse(BaseModel):
    batch_id: str
    total_documents: int
    completed: int
    status: str = Field(description="processing, completed, failed")
    results: List[ComplianceAnalysisResponse] = []
    summary: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    document_type: DocumentType
    file_size: int
    upload_timestamp: datetime
    status: str

class ComplianceQueryResponse(BaseModel):
    question: str
    answer: str
    confidence: Optional[float] = None
    sources: List[str] = []
    response_time: float

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str] = Field(description="Status of dependent services")
    timestamp: datetime

# Database Models (for internal use)
class DocumentCreate(BaseModel):
    filename: str
    file_path: str
    document_type: DocumentType
    file_size: int

class ComplianceResultCreate(BaseModel):
    document_id: str
    classification: ComplianceClassification
    confidence: float
    violations: str = Field(description="JSON string of violations list")
    recommendations: str = Field(description="JSON string of recommendations")
    explanation: Optional[str] = None