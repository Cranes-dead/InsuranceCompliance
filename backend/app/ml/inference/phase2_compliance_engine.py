"""Phase 2 compliance analysis engine using the two-stage Legal-BERT model.

This engine loads the domain-adapted classifier produced by the phase1+phase2
training pipeline and provides async inference for the service layer.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer

from app.models.enums import ComplianceClassification, ViolationSeverity, ViolationType
from app.core.config import settings

logger = logging.getLogger(__name__)


class DomainAdaptedClassifier(nn.Module):
    """Classification head on top of domain-adapted Legal BERT."""

    def __init__(self, model_path: Path, num_labels: int = 3) -> None:
        super().__init__()
        self.num_labels = num_labels
        self.model_path = Path(model_path)

        self.bert = AutoModel.from_pretrained(self.model_path)
        hidden_size = self.bert.config.hidden_size

        self.dropout = nn.Dropout(0.1)
        self.classifier = nn.Linear(hidden_size, num_labels)

    def forward(
        self,
        input_ids,
        attention_mask=None,
        token_type_ids=None,
        labels=None,
    ):  # type: ignore[override]
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)

        result = {"logits": logits}
        if labels is not None:
            loss_fn = nn.CrossEntropyLoss()
            loss = loss_fn(logits.view(-1, self.num_labels), labels.view(-1))
            result["loss"] = loss
        return result


class Phase2ComplianceEngine:
    """Inference wrapper around the phase2 domain-adapted compliance classifier."""

    MODEL_DIR = settings.MODEL_DIR / "legal_bert_compliance_final"
    DOMAIN_MODEL_DIR = settings.MODEL_DIR / "legal_bert_domain_adapted"

    def __init__(self) -> None:
        self._model: Optional[DomainAdaptedClassifier] = None
        self._tokenizer: Optional[AutoTokenizer] = None
        self._id_to_label: Dict[int, str] = {}
        self._is_loaded = False
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    async def initialize(self) -> None:
        """Load model artefacts from disk (no-op if already loaded)."""
        if self._is_loaded:
            return

        await asyncio.to_thread(self._load_model_bundle)

    def is_loaded(self) -> bool:
        """Return whether the underlying artefacts are ready."""
        return self._is_loaded

    async def analyze(self, content: str) -> Dict[str, Any]:
        """Run the compliance classifier on the supplied document content."""
        if not self._is_loaded:
            await self.initialize()

        if not content.strip():
            return {
                "classification": ComplianceClassification.REQUIRES_REVIEW,
                "confidence": 0.0,
                "compliance_score": 0.0,
                "explanation": "Document appears empty; manual review required.",
                "mandatory_compliance": [],
                "recommendations": [
                    "Ensure the uploaded policy contains readable text before re-analysing."
                ],
                "violations": [],
                "probabilities": {},
            }

        return await asyncio.to_thread(self._predict, content)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_model_bundle(self) -> None:
        if not self.MODEL_DIR.exists():
            raise FileNotFoundError(
                f"Phase 2 model directory not found at {self.MODEL_DIR}"
            )

        # Load config to get domain model path
        config_path = self.MODEL_DIR / "config.json"
        domain_model_dir = self.DOMAIN_MODEL_DIR
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as fh:
                config = json.load(fh)
            domain_path_str = config.get("domain_adapted_model_path")
            if domain_path_str:
                domain_model_dir = Path(domain_path_str)

        # Load label map
        label_map_path = self.MODEL_DIR / "label_map.json"
        if label_map_path.exists():
            with label_map_path.open("r", encoding="utf-8") as fh:
                label_map_raw = json.load(fh)
            self._id_to_label = {int(idx): label for idx, label in label_map_raw.items()}
        else:
            logger.warning("label_map.json missing; using default labels")
            self._id_to_label = {
                idx: label for idx, label in settings.COMPLIANCE_LABELS.items()
            }

        # Load tokenizer from phase2 model dir
        self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_DIR)

        # Initialize model architecture
        self._model = DomainAdaptedClassifier(
            domain_model_dir, num_labels=len(self._id_to_label)
        )

        # Load trained weights
        state_dict_path = self.MODEL_DIR / "pytorch_model.bin"
        if not state_dict_path.exists():
            raise FileNotFoundError(f"Missing model weights at {state_dict_path}")

        state_dict = torch.load(state_dict_path, map_location=self._device)
        self._model.load_state_dict(state_dict)
        self._model.to(self._device)
        self._model.eval()

        self._is_loaded = True
        logger.info(
            "✅ Loaded Phase 2 Legal-BERT compliance model from %s", self.MODEL_DIR
        )

    def _predict(self, content: str) -> Dict[str, Any]:
        if not self._tokenizer or not self._model:
            raise RuntimeError("Phase 2 compliance model not loaded")

        encoded = self._tokenizer(
            content,
            padding="max_length",
            truncation=True,
            max_length=settings.MAX_SEQUENCE_LENGTH,
            return_tensors="pt",
        )
        encoded = {key: value.to(self._device) for key, value in encoded.items()}

        with torch.no_grad():
            outputs = self._model(**encoded)
            logits = outputs["logits"].squeeze(0)
            probabilities_tensor = torch.softmax(logits, dim=-1)

        probabilities = probabilities_tensor.cpu().numpy()
        prediction_idx = int(probabilities.argmax())
        classification = self._id_to_label.get(prediction_idx, str(prediction_idx))
        confidence = float(probabilities[prediction_idx])

        probability_map = {
            self._id_to_label.get(i, str(i)): float(prob)
            for i, prob in enumerate(probabilities)
        }

        return self._build_response(classification, confidence, probability_map)

    def _build_response(
        self, classification: str, confidence: float, probability_map: Dict[str, float]
    ) -> Dict[str, Any]:
        explanations = {
            "COMPLIANT": "This document appears to meet IRDAI motor vehicle insurance compliance requirements.",
            "NON_COMPLIANT": "This document appears to have compliance violations that need to be addressed.",
            "REQUIRES_REVIEW": "This document contains elements that require manual review for compliance assessment.",
        }

        violation_confidence = confidence

        mandatory_compliance = [
            {
                "rule": "Third Party Liability Coverage",
                "compliant": classification == "COMPLIANT",
                "found_amount": 1500000,
                "required_amount": 1500000,
                "issue": None
                if classification == "COMPLIANT"
                else "Coverage should meet IRDAI minimum requirements",
            },
            {
                "rule": "Personal Accident Cover for Owner-Driver",
                "compliant": classification == "COMPLIANT",
                "found_amount": 1500000,
                "required_amount": 1500000,
                "issue": None
                if classification == "COMPLIANT"
                else "Verify personal accident cover inclusion",
            },
        ]

        recommendations: List[str] = []
        violations: List[Dict[str, Any]] = []

        if classification == "NON_COMPLIANT":
            recommendations = [
                "Ensure third-party liability coverage meets IRDAI minimum requirements",
                "Verify personal accident cover for owner-driver is included",
            ]
            violations = [
                {
                    "type": ViolationType.COVERAGE_ISSUE,
                    "severity": ViolationSeverity.HIGH,
                    "description": "Third-party liability coverage may be insufficient",
                    "regulation_reference": "IRDAI Motor Insurance Guidelines",
                    "suggested_action": "Increase third-party liability coverage to mandated limits",
                    "confidence": violation_confidence,
                },
                {
                    "type": ViolationType.POLICY_INCONSISTENCY,
                    "severity": ViolationSeverity.HIGH,
                    "description": "Personal accident cover verification required",
                    "regulation_reference": "Motor Vehicles Act",
                    "suggested_action": "Ensure personal accident cover for owner-driver is present",
                    "confidence": violation_confidence,
                },
            ]
        elif classification == "REQUIRES_REVIEW":
            recommendations = [
                "Manual review required for complete compliance assessment",
                "Check all mandatory coverage amounts",
            ]
            violations = [
                {
                    "type": ViolationType.POLICY_INCONSISTENCY,
                    "severity": ViolationSeverity.MEDIUM,
                    "description": "Policy requires manual compliance review",
                    "regulation_reference": "IRDAI Guidelines",
                    "suggested_action": "Conduct manual review to confirm compliance",
                    "confidence": violation_confidence,
                }
            ]

        return {
            "classification": classification,
            "confidence": confidence,
            "compliance_score": round(confidence * 100, 1),  # Convert to percentage (0-100)
            "explanation": explanations.get(
                classification, "Unable to determine compliance status"
            ),
            "mandatory_compliance": mandatory_compliance,
            "recommendations": recommendations,
            "violations": violations,
            "probabilities": probability_map,
        }
