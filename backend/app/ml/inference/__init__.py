"""
ML inference package initialization.

DEAD-03: Collapsed shim chain. Previously:
  __init__ → compliance_engine → simple_compliance_engine → phase2_compliance_engine
Now exports directly from phase2_compliance_engine.
"""
from .phase2_compliance_engine import Phase2ComplianceEngine
from .ollama_client import OllamaClient

# Backward compatibility aliases
ComplianceEngine = Phase2ComplianceEngine
SimpleComplianceEngine = Phase2ComplianceEngine

__all__ = [
    "Phase2ComplianceEngine",
    "ComplianceEngine",
    "SimpleComplianceEngine",
    "OllamaClient"
]