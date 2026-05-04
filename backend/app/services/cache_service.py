"""
Content-hash based caching service with Redis/in-memory backends.

Phase 5: Avoids redundant LLM calls by caching analysis results keyed
on SHA-256 hash of document content. Automatically selects Redis when
REDIS_URL is configured, otherwise falls back to bounded in-memory store.
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any

from app.core import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class InMemoryCacheBackend:
    """Bounded in-memory cache (same eviction pattern as LOGIC-04).
    
    Stores entries with TTL expiration. When full, evicts the entry
    closest to expiration.
    """
    
    def __init__(self, max_size: int = 500):
        self._store: Dict[str, Dict[str, Any]] = {}  # key → {value, expires_at}
        self._max_size = max_size
    
    async def get(self, key: str) -> Optional[dict]:
        """Get a value, returning None if missing or expired."""
        entry = self._store.get(key)
        if not entry:
            return None
        if entry["expires_at"] < time.time():
            del self._store[key]
            return None
        return entry["value"]
    
    async def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        """Set a value with TTL. Evicts oldest entry if at capacity."""
        if len(self._store) >= self._max_size and key not in self._store:
            # Evict the entry closest to expiring
            oldest = min(self._store, key=lambda k: self._store[k]["expires_at"])
            del self._store[oldest]
        self._store[key] = {"value": value, "expires_at": time.time() + ttl}
    
    async def delete(self, key: str) -> None:
        """Delete a key if it exists."""
        self._store.pop(key, None)


class RedisCacheBackend:
    """Redis-backed cache (used when REDIS_URL is configured).
    
    Only instantiated when settings.REDIS_URL is set, so the redis
    package is only imported on demand.
    """
    
    def __init__(self, redis_url: str):
        import redis.asyncio as aioredis
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
    
    async def get(self, key: str) -> Optional[dict]:
        """Get a value from Redis."""
        data = await self._redis.get(key)
        return json.loads(data) if data else None
    
    async def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        """Set a value in Redis with TTL."""
        await self._redis.setex(key, ttl, json.dumps(value, default=str))
    
    async def delete(self, key: str) -> None:
        """Delete a key from Redis."""
        await self._redis.delete(key)


class CacheService:
    """Cache with automatic backend selection.
    
    - If REDIS_URL is set → uses Redis (production)
    - Otherwise → uses in-memory with bounded size (development)
    
    Usage:
        cache = CacheService()
        key = cache.make_document_key(content)
        cached = await cache.get(key)
        if not cached:
            result = await expensive_analysis(...)
            await cache.set(key, result)
    """
    
    def __init__(self):
        if settings.REDIS_URL:
            logger.info("🔴 Cache: Using Redis backend")
            self._backend = RedisCacheBackend(settings.REDIS_URL)
        else:
            logger.info("💾 Cache: Using in-memory backend (set REDIS_URL for Redis)")
            self._backend = InMemoryCacheBackend(max_size=500)
    
    async def get(self, key: str) -> Optional[dict]:
        """Get a cached value."""
        return await self._backend.get(key)
    
    async def set(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
        """Cache a value with optional TTL override."""
        await self._backend.set(key, value, ttl or settings.CACHE_TTL)
    
    async def delete(self, key: str) -> None:
        """Invalidate a cached entry."""
        await self._backend.delete(key)
    
    @staticmethod
    def make_document_key(content: str) -> str:
        """Generate a cache key from document content using SHA-256.
        
        Uses content hash (not filename) so re-uploading the same
        document hits cache regardless of filename.
        """
        return f"analysis:{hashlib.sha256(content.encode()).hexdigest()}"
