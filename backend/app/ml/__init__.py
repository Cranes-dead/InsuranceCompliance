"""
ML package initialization
"""


def __getattr__(name):  # noqa: C901
    if name == "ComplianceEngine":
        from .inference import ComplianceEngine
        return ComplianceEngine
    if name == "Phase2ComplianceEngine":
        from .inference import Phase2ComplianceEngine
        return Phase2ComplianceEngine
    if name == "SimpleComplianceEngine":
        from .inference import SimpleComplianceEngine
        return SimpleComplianceEngine
    if name == "OllamaClient":
        from .inference import OllamaClient
        return OllamaClient
    if name == "LegalBERTComplianceClassifier":
        from .models import LegalBERTComplianceClassifier
        return LegalBERTComplianceClassifier
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ComplianceEngine"
]
