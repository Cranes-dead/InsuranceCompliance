"""
Unit tests for CacheService (Phase 5).

Tests the in-memory backend without Redis dependency.
"""

import pytest
import asyncio
from app.services.cache_service import CacheService, InMemoryCacheBackend


class TestInMemoryCacheBackend:
    """Tests for the bounded in-memory cache backend."""

    @pytest.fixture
    def cache(self):
        return InMemoryCacheBackend(max_size=5)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        await cache.set("key1", {"result": "ok"}, ttl=60)
        val = await cache.get("key1")
        assert val == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_get_missing_key_returns_none(self, cache):
        val = await cache.get("nonexistent")
        assert val is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        await cache.set("key1", {"data": 1}, ttl=60)
        await cache.delete("key1")
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete_missing_key_no_error(self, cache):
        await cache.delete("nonexistent")  # should not raise

    @pytest.mark.asyncio
    async def test_expired_entry_returns_none(self, cache):
        await cache.set("key1", {"data": 1}, ttl=0)  # expires immediately
        # Small sleep to ensure expiry
        await asyncio.sleep(0.01)
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_eviction_at_capacity(self, cache):
        """When at max_size, oldest entry is evicted on insert."""
        for i in range(5):
            await cache.set(f"key{i}", {"i": i}, ttl=3600)
        
        # Cache is full (5 items). Insert one more.
        await cache.set("key_new", {"new": True}, ttl=3600)
        
        # Should still work (one was evicted)
        assert await cache.get("key_new") == {"new": True}
        # Total should not exceed max_size
        assert len(cache._store) <= 5


class TestCacheServiceKey:
    """Tests for the content-hash key generation."""

    def test_same_content_same_key(self):
        key1 = CacheService.make_document_key("hello world")
        key2 = CacheService.make_document_key("hello world")
        assert key1 == key2

    def test_different_content_different_key(self):
        key1 = CacheService.make_document_key("policy A")
        key2 = CacheService.make_document_key("policy B")
        assert key1 != key2

    def test_key_has_prefix(self):
        key = CacheService.make_document_key("test")
        assert key.startswith("analysis:")

    def test_key_is_deterministic_sha256(self):
        import hashlib
        content = "test content"
        expected = f"analysis:{hashlib.sha256(content.encode()).hexdigest()}"
        assert CacheService.make_document_key(content) == expected
