"""
Unit tests for context.py (Phase 6).

Tests request correlation ID via contextvars.
"""

import pytest
import asyncio
from app.core.context import get_request_id, set_request_id, request_id_var


class TestRequestContext:
    """Tests for request correlation ID management."""

    def test_default_is_empty(self):
        """With no set_request_id call, get returns empty string."""
        # Reset to default
        token = request_id_var.set("")
        assert get_request_id() == ""
        request_id_var.reset(token)

    def test_set_generates_uuid4(self):
        rid = set_request_id()
        assert len(rid) == 36  # UUID4 format: 8-4-4-4-12
        assert rid.count("-") == 4

    def test_set_explicit_id(self):
        rid = set_request_id("custom-id-123")
        assert rid == "custom-id-123"
        assert get_request_id() == "custom-id-123"

    def test_get_returns_current(self):
        set_request_id("test-abc")
        assert get_request_id() == "test-abc"

    def test_overwrite_replaces(self):
        set_request_id("first")
        set_request_id("second")
        assert get_request_id() == "second"

    @pytest.mark.asyncio
    async def test_isolation_across_tasks(self):
        """Each asyncio task gets its own context copy."""
        results = {}

        async def worker(name):
            set_request_id(f"task-{name}")
            await asyncio.sleep(0.01)  # yield control
            results[name] = get_request_id()

        await asyncio.gather(worker("a"), worker("b"))
        # Each task should see its own ID (contextvars are task-local)
        assert results["a"] == "task-a"
        assert results["b"] == "task-b"
