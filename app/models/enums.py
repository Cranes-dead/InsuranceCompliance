"""
Enums and constants used throughout the application.
"""

from enum import Enum


class ComplianceClassification(str, Enum):
    """Compliance classification types."""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT" 
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class DocumentType(str, Enum):
    """Supported document types."""
    POLICY = "policy"
    CLAIM = "claim"
    GUIDELINE = "guideline"
    REGULATION = "regulation"
    OTHER = "other"


class AnalysisType(str, Enum):
    """Analysis type options."""
    FULL = "full"
    QUICK = "quick"
    SPECIFIC = "specific"


class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchStatus(str, Enum):
    """Batch analysis status."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ViolationType(str, Enum):
    """Types of compliance violations."""
    REGULATION_BREACH = "REGULATION_BREACH"
    POLICY_INCONSISTENCY = "POLICY_INCONSISTENCY"
    MISSING_INFORMATION = "MISSING_INFORMATION"
    INVALID_TERMS = "INVALID_TERMS"
    COVERAGE_ISSUE = "COVERAGE_ISSUE"
    PREMIUM_VIOLATION = "PREMIUM_VIOLATION"
    OTHER = "OTHER"


class ViolationSeverity(str, Enum):
    """Severity levels for violations."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FileExtension(str, Enum):
    """Supported file extensions."""
    PDF = ".pdf"
    TXT = ".txt"
    DOCX = ".docx"
    DOC = ".doc"


# Constants
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB
MAX_BATCH_SIZE = 100
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100