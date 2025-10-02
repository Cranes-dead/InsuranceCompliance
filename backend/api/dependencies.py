"""
Dependency injection module for API components.
Breaks circular imports by providing a central location for dependencies.
"""

from typing import Optional
from fastapi import HTTPException
from app.services.compliance_service import ComplianceService

# Global service instance
_compliance_service: Optional[ComplianceService] = None


def set_compliance_service(service: ComplianceService) -> None:
    """Set the global compliance service instance."""
    global _compliance_service
    _compliance_service = service


def get_compliance_service() -> ComplianceService:
    """Get the global compliance service instance."""
    global _compliance_service
    if _compliance_service is None:
        raise HTTPException(
            status_code=503,
            detail="Compliance service not initialized"
        )
    return _compliance_service