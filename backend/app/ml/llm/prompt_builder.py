"""
Token-aware prompt builder with fluent API.

Phase 3: Uses the head+tail truncation strategy proven in LOGIC-01 (retriever.py)
to maximize information density within model context windows.

Usage:
    prompt = (PromptBuilder(max_tokens=2048)
        .set_system_role("compliance_analyst")
        .add_policy_text(policy_text)
        .add_regulations(regulations_text)
        .set_output_format()
        .build())
"""

from typing import Optional, Dict, Any, List

from app.core.config import settings


# Approximate tokens-per-word ratio for English text
TOKENS_PER_WORD = 1.3


# ── System Role Preambles ───────────────────────────────────────────────────

ROLE_TEMPLATES = {
    "compliance_analyst": (
        "You are an expert insurance compliance analyst specializing in "
        "Indian motor vehicle insurance regulations (IRDAI/MoRTH). "
        "Analyze policies for regulatory compliance with precision and cite "
        "specific regulations."
    ),
    "chat_advisor": (
        "You are an expert insurance compliance advisor helping users "
        "understand policy compliance analysis results. Provide clear, "
        "actionable answers in plain language suitable for non-experts."
    ),
    "summarizer": (
        "You are a document summarization specialist focused on extracting "
        "compliance-relevant information from insurance policy documents."
    ),
}


# ── JSON Output Schemas ─────────────────────────────────────────────────────

CLASSIFICATION_SCHEMA = """{
    "classification": "COMPLIANT|NON_COMPLIANT|REQUIRES_REVIEW",
    "confidence": 0.0-1.0,
    "compliance_score": 0.0-100.0,
    "violations": [
        {
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "type": "MISSING_COVERAGE|INVALID_EXCLUSION|INADEQUATE_LIMITS|MISLEADING_TERMS|PRICING_VIOLATION",
            "description": "Clear description of the violation",
            "regulation_reference": "Specific regulation violated",
            "recommendation": "How to fix this violation"
        }
    ],
    "mandatory_compliance": [
        {
            "requirement": "Description of requirement",
            "status": "MET|NOT_MET|UNCLEAR",
            "evidence": "Quote from policy showing compliance/non-compliance"
        }
    ],
    "explanation": "Detailed explanation of the classification decision with specific examples and regulation citations",
    "recommendations": [
        "Specific actionable recommendations for compliance"
    ]
}"""

SECTION_ANALYSIS_SCHEMA = """{
    "section_compliant": true/false,
    "issues": ["list of specific issues"],
    "missing_elements": ["required elements not found"],
    "recommendations": ["specific improvements needed"]
}"""


# ── Prompt Builder ──────────────────────────────────────────────────────────

class PromptBuilder:
    """Fluent API for building token-aware prompts.
    
    Dynamically allocates token budgets across prompt sections and uses
    intelligent truncation strategies to maximize information density.
    
    Each prompt section is stored with a sort key (01_, 02_, etc.) to ensure
    deterministic ordering in the final assembled prompt.
    """
    
    def __init__(
        self,
        max_tokens: Optional[int] = None,
        output_reserve: int = 512
    ):
        """Initialize the prompt builder.
        
        Args:
            max_tokens: Total token budget. Defaults to settings.LLM_MAX_TOKENS.
            output_reserve: Tokens reserved for the model's response.
        """
        self._max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self._output_reserve = output_reserve
        self._max_input_words = int(
            (self._max_tokens - output_reserve) / TOKENS_PER_WORD
        )
        self._sections: Dict[str, str] = {}
        self._used_words = 0
    
    # ── Truncation Strategies ───────────────────────────────────────────
    
    def _truncate_head_tail(self, text: str, budget_words: int) -> str:
        """Truncate text keeping head and tail sections.
        
        Proven in LOGIC-01: policy heads contain type/coverage/definitions,
        tails contain terms/compliance clauses/signatures. The middle is
        usually boilerplate that adds less value.
        
        Args:
            text: Full text to truncate.
            budget_words: Maximum words allowed.
            
        Returns:
            Truncated text with head + "[...omitted...]" + tail.
        """
        words = text.split()
        if len(words) <= budget_words:
            return text
        
        head_budget = int(budget_words * 0.65)
        tail_budget = budget_words - head_budget
        
        head = " ".join(words[:head_budget])
        tail = " ".join(words[-tail_budget:])
        
        return f"{head}\n\n[... middle section omitted for brevity ...]\n\n{tail}"
    
    def _truncate_simple(self, text: str, budget_words: int) -> str:
        """Simple truncation keeping the beginning of the text.
        
        Used for regulations (ordered by relevance) and system text
        where the most important content is at the start.
        """
        words = text.split()
        if len(words) <= budget_words:
            return text
        return " ".join(words[:budget_words]) + "\n[... truncated ...]"
    
    def _remaining_budget(self) -> int:
        """Words remaining in the budget."""
        return max(0, self._max_input_words - self._used_words)
    
    # ── Builder Methods ─────────────────────────────────────────────────
    
    def set_system_role(self, role: str = "compliance_analyst") -> "PromptBuilder":
        """Set the system role preamble.
        
        Args:
            role: Key from ROLE_TEMPLATES, or a custom role string.
            
        Returns:
            self for chaining.
        """
        preamble = ROLE_TEMPLATES.get(role, role)
        self._sections["01_system"] = preamble
        self._used_words += len(preamble.split())
        return self
    
    def add_policy_text(
        self,
        text: str,
        budget_pct: float = 0.4
    ) -> "PromptBuilder":
        """Add policy text with head+tail truncation.
        
        Args:
            text: Full policy document text.
            budget_pct: Fraction of total input budget to allocate (0.0-1.0).
            
        Returns:
            self for chaining.
        """
        budget = int(self._max_input_words * budget_pct)
        truncated = self._truncate_head_tail(text, budget)
        self._sections["02_policy"] = f"POLICY TEXT:\n{truncated}"
        self._used_words += len(truncated.split()) + 2  # +2 for header
        return self
    
    def add_regulations(
        self,
        regulations: "str | List[Dict[str, Any]]",
        budget_pct: float = 0.3
    ) -> "PromptBuilder":
        """Add retrieved regulations with budget-aware truncation.
        
        Accepts either pre-formatted text or a list of regulation dicts
        (as returned by the retriever).
        
        Args:
            regulations: Formatted regulation text or list of regulation dicts.
            budget_pct: Fraction of total input budget to allocate.
            
        Returns:
            self for chaining.
        """
        budget = int(self._max_input_words * budget_pct)
        
        if isinstance(regulations, list):
            reg_text = "\n".join(
                f"- [{r.get('metadata', {}).get('source', 'UNKNOWN')}] {r.get('text', '')}"
                for r in regulations
            )
        else:
            reg_text = regulations
        
        truncated = self._truncate_simple(reg_text, budget)
        self._sections["03_regulations"] = f"RELEVANT REGULATIONS:\n{truncated}"
        self._used_words += len(truncated.split()) + 2
        return self
    
    def add_chat_history(
        self,
        messages: List[Dict[str, str]],
        budget_pct: float = 0.2,
        max_messages: int = 5
    ) -> "PromptBuilder":
        """Add chat history (most recent first, budget-aware).
        
        Keeps as many recent messages as fit within the budget.
        
        Args:
            messages: List of {"role": ..., "content": ...} dicts.
            budget_pct: Fraction of total input budget to allocate.
            max_messages: Maximum number of messages to include.
            
        Returns:
            self for chaining.
        """
        budget = int(self._max_input_words * budget_pct)
        recent = messages[-max_messages:]
        
        history_lines = []
        used = 0
        for msg in recent:
            line = f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
            line_words = len(line.split())
            if used + line_words > budget:
                break
            history_lines.append(line)
            used += line_words
        
        if history_lines:
            self._sections["04_history"] = (
                "CONVERSATION HISTORY:\n" + "\n".join(history_lines)
            )
            self._used_words += used + 2
        
        return self
    
    def add_analysis_context(
        self,
        analysis: Dict[str, Any]
    ) -> "PromptBuilder":
        """Add previous analysis results as context (for chat prompts).
        
        Args:
            analysis: Previous compliance analysis result dict.
            
        Returns:
            self for chaining.
        """
        classification = analysis.get("classification", "UNKNOWN")
        confidence = analysis.get("confidence", 0.0)
        explanation = analysis.get("explanation", "No analysis available")
        violations = analysis.get("violations", [])
        
        parts = [
            "PREVIOUS ANALYSIS RESULTS:",
            f"- Classification: {classification}",
            f"- Confidence: {confidence:.1%}",
            f"\nANALYSIS EXPLANATION:\n{explanation[:500]}",
        ]
        
        if violations:
            parts.append("\nKEY VIOLATIONS FOUND:")
            for i, v in enumerate(violations[:5], 1):
                parts.append(
                    f"  {i}. [{v.get('severity', 'UNKNOWN')}] "
                    f"{v.get('description', 'No description')}"
                )
        
        context = "\n".join(parts)
        self._sections["05_analysis"] = context
        self._used_words += len(context.split())
        return self
    
    def add_metadata(
        self,
        metadata: Dict[str, Any]
    ) -> "PromptBuilder":
        """Add policy metadata section.
        
        Args:
            metadata: Dict with keys like 'filename', 'type', 'date'.
            
        Returns:
            self for chaining.
        """
        meta_text = (
            "POLICY METADATA:\n"
            f"- Document Name: {metadata.get('filename', 'Unknown')}\n"
            f"- Document Type: {metadata.get('type', 'Insurance Policy')}\n"
            f"- Analysis Date: {metadata.get('date', 'Not specified')}"
        )
        self._sections["02a_metadata"] = meta_text
        self._used_words += len(meta_text.split())
        return self
    
    def add_task_instructions(self, instructions: str) -> "PromptBuilder":
        """Add custom task-specific instructions.
        
        Args:
            instructions: Free-form instruction text.
            
        Returns:
            self for chaining.
        """
        self._sections["06_task"] = instructions
        self._used_words += len(instructions.split())
        return self
    
    def set_output_format(
        self,
        schema: str = CLASSIFICATION_SCHEMA
    ) -> "PromptBuilder":
        """Set the expected output JSON format.
        
        Args:
            schema: JSON schema string showing expected output structure.
            
        Returns:
            self for chaining.
        """
        section = (
            "OUTPUT FORMAT (respond in valid JSON only):\n"
            f"{schema}\n\n"
            "Provide your analysis in valid JSON format only. "
            "Be thorough, cite specific regulations, and provide "
            "clear evidence for your conclusions."
        )
        self._sections["07_output"] = section
        self._used_words += len(section.split())
        return self
    
    # ── Build & Inspect ─────────────────────────────────────────────────
    
    def build(self) -> str:
        """Assemble the final prompt from all sections.
        
        Sections are ordered by their sort key (01_system, 02_policy, etc.)
        to ensure deterministic output.
        
        Returns:
            Complete prompt string.
        """
        ordered = sorted(self._sections.items(), key=lambda x: x[0])
        return "\n\n".join(content for _, content in ordered)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get prompt composition statistics for debugging.
        
        Returns:
            Dict with token budget usage, section list, and estimates.
        """
        return {
            "max_tokens": self._max_tokens,
            "output_reserve": self._output_reserve,
            "max_input_words": self._max_input_words,
            "used_words": self._used_words,
            "remaining_words": self._remaining_budget(),
            "sections": list(self._sections.keys()),
            "estimated_input_tokens": int(self._used_words * TOKENS_PER_WORD),
        }
