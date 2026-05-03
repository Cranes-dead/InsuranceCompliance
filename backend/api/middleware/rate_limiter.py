"""
IP-based rate limiting middleware.

Phase 4: Sliding window rate limiter using in-memory store with bounded
dictionary (same pattern as LOGIC-04). Uses Starlette middleware protocol.
"""

import time
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core import get_logger

logger = get_logger(__name__)

# Paths exempt from rate limiting
EXEMPT_PATHS = frozenset({
    "/health", "/", "/docs", "/redoc", "/openapi.json",
})


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """IP-based sliding window rate limiter.
    
    Tracks request timestamps per IP and rejects requests that exceed
    the configured limit within the time window.
    
    Args:
        app: The ASGI application.
        max_requests: Maximum requests allowed per window.
        window_seconds: Time window in seconds.
        max_tracked_ips: Maximum IPs to track (prevents memory exhaustion).
    """
    
    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: int = 60,
        max_tracked_ips: int = 10000,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_tracked_ips = max_tracked_ips
        # Store: {ip: [timestamps]}
        self._store: Dict[str, List[float]] = {}
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For behind proxies."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # First IP in the chain is the real client
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _is_allowed(self, ip: str) -> Tuple[bool, int]:
        """Check if the IP is within rate limits.
        
        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Get or create timestamp list
        timestamps = self._store.get(ip, [])
        
        # Remove expired timestamps
        timestamps = [t for t in timestamps if t > cutoff]
        
        # Check limit
        remaining = self.max_requests - len(timestamps)
        if remaining <= 0:
            self._store[ip] = timestamps
            return False, 0
        
        # Record this request
        timestamps.append(now)
        self._store[ip] = timestamps
        
        # Evict oldest IPs if store is too large (bounded like LOGIC-04)
        if len(self._store) > self.max_tracked_ips:
            oldest_ip = min(
                self._store,
                key=lambda k: self._store[k][-1] if self._store[k] else 0
            )
            del self._store[oldest_ip]
        
        return True, remaining - 1
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter."""
        # Skip exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        
        ip = self._get_client_ip(request)
        allowed, remaining = self._is_allowed(ip)
        
        if not allowed:
            logger.warning(f"🚫 Rate limit exceeded for IP: {ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds.",
                        "details": {"retry_after_seconds": self.window_seconds}
                    }
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
