"""
Custom exceptions for the Insurance Compliance System.
"""

from typing import Any, Dict, Optional


class ComplianceSystemException(Exception):
    """Base exception class for the compliance system."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class DocumentProcessingError(ComplianceSystemException):
    """Raised when document processing fails."""
    pass


class ModelInferenceError(ComplianceSystemException):
    """Raised when ML model inference fails."""
    pass


class FileValidationError(ComplianceSystemException):
    """Raised when file validation fails."""
    pass


class DatabaseError(ComplianceSystemException):
    """Raised when database operations fail."""
    pass


class ExternalServiceError(ComplianceSystemException):
    """Raised when external service calls fail."""
    pass


class ConfigurationError(ComplianceSystemException):
    """Raised when configuration is invalid."""
    pass


class AuthenticationError(ComplianceSystemException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(ComplianceSystemException):
    """Raised when authorization fails."""
    pass