"""
Services package initialization
"""


def __getattr__(name):
    if name == "ComplianceService":
        from .compliance_service import ComplianceService
        return ComplianceService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ComplianceService"
]
