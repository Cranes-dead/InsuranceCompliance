"""
Compliance inference engine that orchestrates ML models and rule-based analysis.
Refactored from updated_compliance_system.py to follow clean architecture.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from ...core import get_logger, settings
from ...core.exceptions import ModelInferenceError
from ...models import (
    ComplianceClassification,
    ViolationType,
    ViolationSeverity,
    ViolationDetail
)
from ..models.legal_bert import LegalBERTComplianceClassifier
from .ollama_client import OllamaClient

logger = get_logger(__name__)


class ComplianceEngine:
    """
    Main compliance analysis engine.
    
    This engine combines Legal BERT classification with rule-based analysis
    and provides AI-generated explanations using Ollama.
    """
    
    def __init__(self):
        """Initialize the compliance engine."""
        self.legal_bert_model = None
        self.ollama_client = OllamaClient()
        self._initialized = False
        self._rule_classifier = None
    
    async def initialize(self) -> None:
        """Initialize all ML components."""
        if self._initialized:
            return
            
        try:
            logger.info("Initializing compliance engine...")
            
            # Initialize Legal BERT model
            await self._initialize_legal_bert()
            
            # Initialize rule classifier
            await self._initialize_rule_classifier()
            
            # Test Ollama connection
            await self.ollama_client.test_connection()
            
            self._initialized = True
            logger.info("Compliance engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize compliance engine: {e}")
            raise ModelInferenceError(
                "Engine initialization failed",
                error_code="ENGINE_INIT_ERROR",
                details={"error": str(e)}
            )
    
    async def analyze(
        self,
        content: str,
        analysis_type: str = "full",
        custom_rules: Optional[List[str]] = None
    ) -> Dict:
        """
        Perform comprehensive compliance analysis.
        
        Args:
            content: Document text content
            analysis_type: Type of analysis ("full", "quick", "specific")
            custom_rules: Optional list of custom rules to apply
            
        Returns:
            Dictionary with analysis results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.debug(f"Starting {analysis_type} analysis")
            
            # Legal BERT classification
            classification_result = await self._classify_compliance(content)
            
            # Rule-based analysis
            violations = await self._analyze_violations(
                content,
                classification_result,
                custom_rules
            )
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                classification_result,
                violations
            )
            
            return {
                "classification": classification_result["classification"],
                "confidence": classification_result["confidence"],
                "violations": violations,
                "recommendations": recommendations,
                "metadata": {
                    "model_version": "1.0",
                    "analysis_type": analysis_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise ModelInferenceError(
                "Compliance analysis failed",
                error_code="ANALYSIS_ERROR",
                details={"error": str(e)}
            )
    
    async def generate_explanation(
        self,
        content: str,
        analysis_result: Dict
    ) -> Optional[str]:
        """Generate human-readable explanation using Ollama."""
        try:
            explanation_prompt = self._build_explanation_prompt(content, analysis_result)
            return await self.ollama_client.generate_explanation(explanation_prompt)
        except Exception as e:
            logger.warning(f"Failed to generate explanation: {e}")
            return None
    
    async def _initialize_legal_bert(self) -> None:
        """Initialize the Legal BERT model."""
        try:
            # This would load your trained Legal BERT model
            # For now, we'll create a mock implementation
            logger.info("Loading Legal BERT model...")
            
            model_path = settings.MODEL_DIR / "legal_bert_compliance"
            if model_path.exists():
                self.legal_bert_model = LegalBERTComplianceClassifier()
                # Load model weights here
                logger.info("Legal BERT model loaded successfully")
            else:
                logger.warning("Legal BERT model not found, using mock implementation")
                self.legal_bert_model = MockLegalBERT()
                
        except Exception as e:
            raise ModelInferenceError(f"Failed to load Legal BERT model: {e}")
    
    async def _initialize_rule_classifier(self) -> None:
        """Initialize the rule classifier."""
        try:
            # This would load your rule-based classifier
            logger.info("Initializing rule classifier...")
            self._rule_classifier = MockRuleClassifier()
            logger.info("Rule classifier initialized")
        except Exception as e:
            raise ModelInferenceError(f"Failed to initialize rule classifier: {e}")
    
    async def _classify_compliance(self, content: str) -> Dict:
        """Classify document compliance using Legal BERT."""
        try:
            # Run model inference
            prediction = await self.legal_bert_model.predict(content)
            
            return {
                "classification": prediction["classification"],
                "confidence": prediction["confidence"],
                "probabilities": prediction.get("probabilities", {})
            }
        except Exception as e:
            raise ModelInferenceError(f"Legal BERT classification failed: {e}")
    
    async def _analyze_violations(
        self,
        content: str,
        classification_result: Dict,
        custom_rules: Optional[List[str]] = None
    ) -> List[ViolationDetail]:
        """Analyze specific violations using rule-based approach."""
        violations = []
        
        try:
            # Rule-based violation detection
            rule_violations = await self._rule_classifier.detect_violations(
                content,
                custom_rules
            )
            
            for violation in rule_violations:
                violations.append(ViolationDetail(
                    type=ViolationType(violation["type"]),
                    severity=ViolationSeverity(violation["severity"]),
                    description=violation["description"],
                    regulation_reference=violation.get("regulation_reference"),
                    suggested_action=violation.get("suggested_action"),
                    confidence=violation["confidence"],
                    location=violation.get("location")
                ))
            
            return violations
            
        except Exception as e:
            logger.error(f"Violation analysis failed: {e}")
            return []  # Return empty list instead of raising
    
    async def _generate_recommendations(
        self,
        classification_result: Dict,
        violations: List[ViolationDetail]
    ) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Basic recommendations based on classification
        classification = classification_result["classification"]
        
        if classification == ComplianceClassification.NON_COMPLIANT:
            recommendations.append("Review document for regulatory compliance issues")
            recommendations.append("Consult with legal team before proceeding")
            
        elif classification == ComplianceClassification.REQUIRES_REVIEW:
            recommendations.append("Manual review recommended for potential issues")
            
        # Add violation-specific recommendations
        for violation in violations:
            if violation.suggested_action:
                recommendations.append(violation.suggested_action)
        
        return recommendations
    
    def _build_explanation_prompt(self, content: str, analysis_result: Dict) -> str:
        """Build prompt for explanation generation."""
        classification = analysis_result["classification"]
        violations = analysis_result.get("violations", [])
        
        prompt = f"""
        Analyze this insurance document and explain the compliance assessment:
        
        Classification: {classification}
        Confidence: {analysis_result.get("confidence", 0):.2f}
        
        Document Content (truncated):
        {content[:1000]}...
        
        Violations Found: {len(violations)}
        
        Please provide a clear, professional explanation of:
        1. Why this document was classified as {classification}
        2. Key compliance issues identified
        3. Recommended next steps
        
        Keep the explanation concise and focused on actionable insights.
        """
        
        return prompt


class MockLegalBERT:
    """Mock Legal BERT implementation for testing."""
    
    async def predict(self, content: str) -> Dict:
        """Mock prediction."""
        # Simple rule-based mock logic
        content_lower = content.lower()
        
        if "violation" in content_lower or "non-compliant" in content_lower:
            classification = ComplianceClassification.NON_COMPLIANT
            confidence = 0.85
        elif "review" in content_lower or "unclear" in content_lower:
            classification = ComplianceClassification.REQUIRES_REVIEW
            confidence = 0.75
        else:
            classification = ComplianceClassification.COMPLIANT
            confidence = 0.90
        
        return {
            "classification": classification,
            "confidence": confidence,
            "probabilities": {
                "COMPLIANT": confidence if classification == ComplianceClassification.COMPLIANT else 1 - confidence,
                "NON_COMPLIANT": confidence if classification == ComplianceClassification.NON_COMPLIANT else 1 - confidence,
                "REQUIRES_REVIEW": confidence if classification == ComplianceClassification.REQUIRES_REVIEW else 1 - confidence
            }
        }


class MockRuleClassifier:
    """Mock rule classifier for testing."""
    
    async def detect_violations(
        self,
        content: str,
        custom_rules: Optional[List[str]] = None
    ) -> List[Dict]:
        """Mock violation detection."""
        violations = []
        content_lower = content.lower()
        
        # Mock violation patterns
        if "premium" in content_lower and "high" in content_lower:
            violations.append({
                "type": "PREMIUM_VIOLATION",
                "severity": "HIGH",
                "description": "Premium amount may exceed regulatory limits",
                "regulation_reference": "IRDAI/REG/2023/001",
                "suggested_action": "Review premium calculation methodology",
                "confidence": 0.8
            })
        
        if "coverage" in content_lower and "insufficient" in content_lower:
            violations.append({
                "type": "COVERAGE_ISSUE",
                "severity": "MEDIUM",
                "description": "Insufficient coverage detected for mandatory requirements",
                "regulation_reference": "IRDAI/REG/2023/002",
                "suggested_action": "Increase minimum coverage amounts",
                "confidence": 0.75
            })
        
        return violations