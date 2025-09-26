"""
Refactored Legal BERT model for compliance classification.
"""

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel, AutoConfig
from typing import Dict, List, Optional, Any
import numpy as np
from pathlib import Path
import json

from ...core import get_logger, settings
from ...core.exceptions import ModelInferenceError
from ...models import ComplianceClassification

logger = get_logger(__name__)


class LegalBERTComplianceClassifier(nn.Module):
    """
    Legal BERT model fine-tuned for insurance compliance classification.
    
    This model classifies documents into:
    - COMPLIANT: Document meets all regulatory requirements
    - NON_COMPLIANT: Document has clear violations
    - REQUIRES_REVIEW: Document needs manual review
    """
    
    def __init__(
        self,
        model_name: str = "nlpaueb/legal-bert-base-uncased",
        num_labels: int = 3,
        model_path: Optional[Path] = None
    ):
        super().__init__()
        self.num_labels = num_labels
        self.model_name = model_name
        self.model_path = model_path or settings.MODEL_DIR / "legal_bert_compliance"
        
        # Load configuration
        self.config = None
        self.tokenizer = None
        self.bert = None
        self.classifier = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Label mappings
        self.id2label = {
            0: ComplianceClassification.COMPLIANT,
            1: ComplianceClassification.NON_COMPLIANT,
            2: ComplianceClassification.REQUIRES_REVIEW
        }
        self.label2id = {v: k for k, v in self.id2label.items()}
    
    def _build_model(self):
        """Build the model architecture."""
        try:
            # Load pre-trained Legal BERT
            self.config = AutoConfig.from_pretrained(
                self.model_name,
                num_labels=self.num_labels
            )
            self.bert = AutoModel.from_pretrained(
                self.model_name,
                config=self.config
            )
            
            # Classification head
            self.dropout = nn.Dropout(self.config.hidden_dropout_prob)
            self.classifier = nn.Linear(self.config.hidden_size, self.num_labels)
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            logger.info("Legal BERT model architecture built successfully")
            
        except Exception as e:
            raise ModelInferenceError(
                f"Failed to build Legal BERT model: {e}",
                error_code="MODEL_BUILD_ERROR"
            )
    
    def forward(self, input_ids, attention_mask=None, labels=None):
        """Forward pass through the model."""
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        
        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
        
        return {"loss": loss, "logits": logits}
    
    def load_model(self) -> None:
        """Load trained model weights."""
        try:
            if not self.config:
                self._build_model()
            
            # Try to load fine-tuned weights
            model_file = self.model_path / "pytorch_model.bin"
            if model_file.exists():
                logger.info(f"Loading fine-tuned model from {model_file}")
                state_dict = torch.load(model_file, map_location=self._device)
                self.load_state_dict(state_dict)
            else:
                logger.warning("Fine-tuned model not found, using base Legal BERT")
            
            self.to(self._device)
            self.eval()
            logger.info("Legal BERT model loaded successfully")
            
        except Exception as e:
            raise ModelInferenceError(
                f"Failed to load Legal BERT model: {e}",
                error_code="MODEL_LOAD_ERROR"
            )
    
    async def predict(
        self,
        text: str,
        max_length: int = 512,
        return_probabilities: bool = True
    ) -> Dict[str, Any]:
        """
        Predict compliance classification for text.
        
        Args:
            text: Input text to classify
            max_length: Maximum sequence length
            return_probabilities: Whether to return class probabilities
            
        Returns:
            Dictionary with prediction results
        """
        try:
            if not self.tokenizer:
                self.load_model()
            
            # Tokenize input
            inputs = self.tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=max_length,
                return_tensors="pt"
            )
            
            # Move to device
            input_ids = inputs["input_ids"].to(self._device)
            attention_mask = inputs["attention_mask"].to(self._device)
            
            # Inference
            with torch.no_grad():
                outputs = self.forward(input_ids, attention_mask)
                logits = outputs["logits"]
                probabilities = torch.softmax(logits, dim=-1)
            
            # Get predictions
            predicted_id = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_id].item()
            classification = self.id2label[predicted_id]
            
            result = {
                "classification": classification,
                "confidence": float(confidence),
                "predicted_id": predicted_id
            }
            
            if return_probabilities:
                probs = probabilities[0].cpu().numpy()
                result["probabilities"] = {
                    self.id2label[i]: float(probs[i]) for i in range(len(probs))
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise ModelInferenceError(
                f"Legal BERT prediction failed: {e}",
                error_code="PREDICTION_ERROR"
            )
    
    async def predict_batch(
        self,
        texts: List[str],
        max_length: int = 512,
        batch_size: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Predict compliance classification for multiple texts.
        
        Args:
            texts: List of texts to classify
            max_length: Maximum sequence length
            batch_size: Batch size for processing
            
        Returns:
            List of prediction results
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_results = []
            
            for text in batch_texts:
                result = await self.predict(text, max_length)
                batch_results.append(result)
            
            results.extend(batch_results)
        
        return results
    
    def save_model(self, save_path: Path) -> None:
        """Save model weights and configuration."""
        try:
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Save model weights
            torch.save(self.state_dict(), save_path / "pytorch_model.bin")
            
            # Save configuration
            if self.config:
                self.config.save_pretrained(save_path)
            
            # Save tokenizer
            if self.tokenizer:
                self.tokenizer.save_pretrained(save_path)
            
            # Save label mappings
            with open(save_path / "label_map.json", "w") as f:
                json.dump(self.id2label, f, indent=2)
            
            logger.info(f"Model saved to {save_path}")
            
        except Exception as e:
            raise ModelInferenceError(
                f"Failed to save model: {e}",
                error_code="MODEL_SAVE_ERROR"
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model_name": self.model_name,
            "num_labels": self.num_labels,
            "device": str(self._device),
            "labels": list(self.id2label.values()),
            "model_path": str(self.model_path) if self.model_path else None
        }