"""
Optional API key authentication middleware.

Phase 4: Validates Authorization: Bearer <key> against configured API keys.
Completely DISABLED when API_KEYS is empty/None (backward compatible).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional, Set

from app.core import get_logger

logger = get_logger(__name__)

# Paths that never require authentication
PUBLIC_PATHS = frozenset({
    "/health", "/", "/docs", "/redoc", "/openapi.json",
})


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Optional API key authentication middleware.
    
    When api_keys is None or empty, authentication is completely disabled
    and all requests pass through (backward compatible).
    
    When api_keys is set, requests must include:
        Authorization: Bearer <valid-key>
    
    Args:
        app: The ASGI application.
        api_keys: Set of valid API keys, or None to disable auth.
    """
    
    def __init__(self, app, api_keys: Optional[Set[str]] = None):
        super().__init__(app)
        self.api_keys = api_keys
        
        if self.api_keys:
            logger.info(f"🔐 API key auth enabled ({len(self.api_keys)} key(s) configured)")
        else:
            logger.info("🔓 API key auth disabled (no API_KEYS configured)")
    
    async def dispatch(self, request: Request, call_next):
        """Validate API key if auth is enabled."""
        # Auth disabled — pass everything through
        if not self.api_keys:
            return await call_next(request)
        
        # Public paths — skip auth
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Also skip preflight CORS requests
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Extract and validate API key
        auth_header = request.headers.get("authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "error_code": "AUTHENTICATION_REQUIRED",
                        "message": "Missing or invalid Authorization header. Use: Authorization: Bearer <api-key>",
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        api_key = auth_header[7:]  # Strip "Bearer "
        
        if api_key not in self.api_keys:
            logger.warning(f"🚫 Invalid API key attempt from {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "error_code": "INVALID_API_KEY",
                        "message": "Invalid API key.",
                    }
                },
            )
        
        return await call_next(request)
