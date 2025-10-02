from typing import Dict, Any
from ...core import get_logger
from ...core.exceptions import ModelInferenceError

logger = get_logger(__name__)

class LegalBERTClassifier:
    def __init__(self, model_name="nlpaueb/legal-bert-base-uncased"):
        self.model_name = model_name
        
    def load_model(self, model_path: str):
        logger.info("Mock LegalBERT loaded")
        
    def classify_text(self, text: str) -> Dict[str, Any]:
        return {
            "label": "COMPLIANT",
            "confidence": 0.87,
            "probabilities": {"COMPLIANT": 0.87, "NON_COMPLIANT": 0.08, "REQUIRES_REVIEW": 0.05}
        }

LegalBERTComplianceClassifier = LegalBERTClassifier
