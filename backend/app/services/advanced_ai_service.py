"""Compatibility stub for the removed advanced AI service.

The streamlined system no longer ships the transformer/Ollama stack. This module
remains solely so legacy imports do not break. All methods now return
informational defaults that point callers to the primary compliance pipeline.
"""

from __future__ import annotations

from typing import Any, Dict

from app.models.enums import ComplianceClassification

__all__ = ["AdvancedAIService"]


class AdvancedAIService:  # pragma: no cover - legacy compatibility stub
    """Minimal implementation that advertises the absence of advanced AI."""

    def __init__(self, use_advanced_ai: bool = False) -> None:
        # Advanced features are no longer packaged; keep flag for API parity.
        self.use_advanced_ai = bool(use_advanced_ai and False)
        self._initialized = False

    async def initialize(self) -> None:
        """Mark the stub as initialized."""
        self._initialized = True

    async def analyze_document(self, content: str) -> Dict[str, Any]:
        """Return a deterministic placeholder response indicating feature removal."""
        if not self._initialized:
            await self.initialize()

        return {
            "classification": ComplianceClassification.REQUIRES_REVIEW,
            "confidence": 0.0,
            "violations": [],
            "recommendations": [
                "Advanced AI analysis unavailable in streamlined configuration.",
                "Proceed with manual compliance review.",
            ],
            "explanation": "Advanced AI features have been disabled in this build.",
            "ai_powered": False,
            "model_info": {
                "classifier": "advanced-ai-disabled",
                "version": "0.0.0",
            },
        }

    async def chat_with_policy(self, query: str, policy_content: str) -> str:
        """Maintain legacy signature but clearly communicate feature removal."""
        if not self._initialized:
            await self.initialize()
        return (
            "Interactive policy chat requires the deprecated Advanced AI stack and is no "
            "longer available in this streamlined deployment."
        )

    def get_ai_status(self) -> Dict[str, Any]:
        """Expose simple status flags for diagnostics."""
        return {
            "advanced_ai_available": False,
            "legal_bert_loaded": False,
            "ollama_connected": False,
            "simple_model_loaded": False,
            "initialized": self._initialized,
            "features": {
                "classification": False,
                "explanation": False,
                "interactive_chat": False,
                "advanced_analysis": False,
            },
        }

    async def shutdown(self) -> None:
        """No-op retained for API compatibility."""
        self._initialized = False