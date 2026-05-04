"""
Unit tests for PromptBuilder (Phase 3).

Tests token budgeting, truncation strategies, and fluent API.
"""

import pytest
from app.ml.llm.prompt_builder import PromptBuilder, TOKENS_PER_WORD


class TestPromptBuilderTruncation:
    """Tests for truncation strategies."""

    def test_short_text_not_truncated(self):
        b = PromptBuilder(max_tokens=2048)
        b.add_policy_text("short policy text", budget_pct=0.4)
        prompt = b.build()
        assert "omitted" not in prompt
        assert "short policy text" in prompt

    def test_long_text_head_tail_truncated(self):
        long_text = "word " * 5000
        b = PromptBuilder(max_tokens=1024)
        b.add_policy_text(long_text, budget_pct=0.4)
        prompt = b.build()
        assert "omitted" in prompt

    def test_head_tail_keeps_beginning_and_end(self):
        words = [f"w{i}" for i in range(1000)]
        text = " ".join(words)
        b = PromptBuilder(max_tokens=512)
        b.add_policy_text(text, budget_pct=0.4)
        prompt = b.build()
        # Head should contain w0
        assert "w0" in prompt
        # Tail should contain the last word
        assert "w999" in prompt

    def test_regulations_simple_truncation(self):
        long_regs = "regulation " * 3000
        b = PromptBuilder(max_tokens=1024)
        b.add_regulations(long_regs, budget_pct=0.3)
        prompt = b.build()
        assert "truncated" in prompt


class TestPromptBuilderBudget:
    """Tests for token budget management."""

    def test_budget_calculation(self):
        b = PromptBuilder(max_tokens=1000, output_reserve=200)
        stats = b.get_stats()
        assert stats["max_tokens"] == 1000
        assert stats["output_reserve"] == 200
        assert stats["max_input_words"] == int(800 / TOKENS_PER_WORD)

    def test_used_words_tracking(self):
        b = PromptBuilder(max_tokens=2048)
        assert b.get_stats()["used_words"] == 0
        b.set_system_role("compliance_analyst")
        assert b.get_stats()["used_words"] > 0

    def test_remaining_budget_decreases(self):
        b = PromptBuilder(max_tokens=2048)
        initial = b.get_stats()["remaining_words"]
        b.set_system_role("compliance_analyst")
        after = b.get_stats()["remaining_words"]
        assert after < initial

    def test_sections_listed_in_stats(self):
        b = PromptBuilder(max_tokens=2048)
        b.set_system_role("compliance_analyst")
        b.add_policy_text("test", budget_pct=0.4)
        stats = b.get_stats()
        assert "01_system" in stats["sections"]
        assert "02_policy" in stats["sections"]


class TestPromptBuilderFluentAPI:
    """Tests for fluent API chaining."""

    def test_chaining_returns_self(self):
        b = PromptBuilder(max_tokens=2048)
        result = b.set_system_role("compliance_analyst")
        assert result is b

    def test_full_chain_produces_output(self):
        prompt = (
            PromptBuilder(max_tokens=2048)
            .set_system_role("compliance_analyst")
            .add_policy_text("test policy", budget_pct=0.4)
            .add_regulations("test regulation", budget_pct=0.3)
            .set_output_format()
            .build()
        )
        assert len(prompt) > 100
        assert "compliance" in prompt.lower()
        assert "JSON" in prompt

    def test_sections_ordered_deterministically(self):
        prompt = (
            PromptBuilder(max_tokens=2048)
            .add_regulations("regs here", budget_pct=0.3)
            .set_system_role("compliance_analyst")
            .add_policy_text("policy here", budget_pct=0.4)
            .build()
        )
        # System role (01_) should appear before policy (02_) before regs (03_)
        sys_pos = prompt.find("compliance")
        policy_pos = prompt.find("policy here")
        regs_pos = prompt.find("regs here")
        assert sys_pos < policy_pos < regs_pos


class TestPromptBuilderChatHistory:
    """Tests for chat history budget handling."""

    def test_empty_history_no_section(self):
        b = PromptBuilder(max_tokens=2048)
        b.add_chat_history([], budget_pct=0.2)
        assert "04_history" not in b.get_stats()["sections"]

    def test_history_within_budget(self):
        msgs = [{"role": "user", "content": "word " * 200} for _ in range(10)]
        b = PromptBuilder(max_tokens=500, output_reserve=100)
        b.add_chat_history(msgs, budget_pct=0.3)
        stats = b.get_stats()
        assert stats["used_words"] < stats["max_input_words"]

    def test_max_messages_respected(self):
        msgs = [{"role": "user", "content": f"msg{i}"} for i in range(20)]
        b = PromptBuilder(max_tokens=4096)
        b.add_chat_history(msgs, max_messages=3)
        prompt = b.build()
        # Only last 3 messages should be included
        assert "msg17" in prompt
        assert "msg18" in prompt
        assert "msg19" in prompt
        assert "msg0" not in prompt


class TestPromptBuilderAnalysisContext:
    """Tests for analysis context injection."""

    def test_analysis_context_added(self, sample_analysis_result):
        b = PromptBuilder(max_tokens=2048)
        b.add_analysis_context(sample_analysis_result)
        prompt = b.build()
        assert "NON_COMPLIANT" in prompt
        assert "CRITICAL" in prompt
        assert "Third party" in prompt
