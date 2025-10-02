"""Manual sanity test for the two-phase Legal-BERT compliance model.

This script loads the domain-adapted classifier produced by
`phase2_classification_training.py`, parses one of the sample policy PDFs,
and prints the model's prediction along with per-class probabilities.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.processing.parsers.document_parser import DocumentParser  # noqa: E402

LOGGER = logging.getLogger("phase2_model_test")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

MODELS_DIR = BACKEND_ROOT / "models"
PHASE2_MODEL_DIR = MODELS_DIR / "legal_bert_compliance_final"
PHASE1_MODEL_DIR = MODELS_DIR / "legal_bert_domain_adapted"
SAMPLE_POLICY = BACKEND_ROOT / "test_samples" / "sample_policy_compliant.pdf"
MAX_SEQUENCE_LENGTH = 512


class DomainAdaptedClassifier(nn.Module):
    """Classification head stacked on top of a domain-adapted Legal-BERT backbone."""

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


@dataclass
class Phase2ComplianceModel:
    """Wrapper that loads the trained two-phase Legal-BERT classifier."""

    model_dir: Path
    domain_model_dir: Path
    label_map: Dict[int, str]
    device: torch.device

    @classmethod
    def load(cls, model_dir: Path = PHASE2_MODEL_DIR) -> "Phase2ComplianceModel":
        if not model_dir.exists():
            raise FileNotFoundError(
                f"Phase 2 model directory not found at {model_dir}. Did you run phase2_classification_training.py?"
            )

        config_path = model_dir / "config.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as fh:
                config = json.load(fh)
            domain_model_dir = Path(config.get("domain_adapted_model_path", PHASE1_MODEL_DIR))
        else:
            LOGGER.warning("config.json missing in %s; defaulting to %s", model_dir, PHASE1_MODEL_DIR)
            domain_model_dir = PHASE1_MODEL_DIR

        label_map_path = model_dir / "label_map.json"
        if label_map_path.exists():
            with label_map_path.open("r", encoding="utf-8") as fh:
                label_map_raw = json.load(fh)
            label_map = {int(idx): label for idx, label in label_map_raw.items()}
        else:
            LOGGER.warning("label_map.json missing in %s; using default IDs", model_dir)
            label_map = {0: "COMPLIANT", 1: "NON_COMPLIANT", 2: "REQUIRES_REVIEW"}

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        LOGGER.info("Using device: %s", device)

        model = DomainAdaptedClassifier(domain_model_dir, num_labels=len(label_map))
        state_dict_path = model_dir / "pytorch_model.bin"
        if not state_dict_path.exists():
            raise FileNotFoundError(f"Missing model weights at {state_dict_path}")

        state_dict = torch.load(state_dict_path, map_location=device)
        model.load_state_dict(state_dict)
        model.to(device)
        model.eval()

        tokenizer = AutoTokenizer.from_pretrained(model_dir)

        return cls(
            model_dir=model_dir,
            domain_model_dir=domain_model_dir,
            label_map=label_map,
            device=device,
        )._with_model(model, tokenizer)

    def _with_model(self, model: DomainAdaptedClassifier, tokenizer: AutoTokenizer) -> "Phase2ComplianceModel":
        self._model = model
        self._tokenizer = tokenizer
        return self

    def predict(self, text: str) -> Dict[str, float | str | Dict[str, float]]:
        encoded = self._tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=MAX_SEQUENCE_LENGTH,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}

        with torch.no_grad():
            outputs = self._model(**encoded)
            logits = outputs["logits"]
            probabilities = torch.softmax(logits, dim=-1).squeeze(0)

        confidence, predicted_idx = torch.max(probabilities, dim=0)
        predicted_idx = int(predicted_idx.item())

        probability_map = {
            self.label_map.get(idx, str(idx)): float(probabilities[idx].item())
            for idx in range(probabilities.shape[0])
        }

        return {
            "classification": self.label_map.get(predicted_idx, str(predicted_idx)),
            "confidence": float(confidence.item()),
            "probabilities": probability_map,
        }


async def parse_sample() -> str:
    parser = DocumentParser()
    return await parser.parse(str(SAMPLE_POLICY))


async def main() -> None:
    LOGGER.info("Loading Phase 2 Legal-BERT compliance model from %s", PHASE2_MODEL_DIR)
    model = Phase2ComplianceModel.load(PHASE2_MODEL_DIR)

    if not SAMPLE_POLICY.exists():
        raise FileNotFoundError(f"Sample PDF not found at {SAMPLE_POLICY}")

    LOGGER.info("Parsing sample policy: %s", SAMPLE_POLICY.name)
    text = await parse_sample()
    LOGGER.info("Sample length: %d characters", len(text))

    LOGGER.info("Running inference...")
    result = model.predict(text)

    print("\n📊 Phase 2 Compliance Model Prediction")
    print("=" * 50)
    print(f"Classification: {result['classification']}")
    print(f"Confidence: {result['confidence']:.3f}")

    print("\nClass probabilities:")
    for label, prob in result["probabilities"].items():
        print(f"  - {label}: {prob:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
