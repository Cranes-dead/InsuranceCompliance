"""
Thread-safe request context using Python contextvars.

Phase 6: Provides request correlation IDs that automatically propagate
through async handlers and asyncio.to_thread() calls.
"""

import contextvars
from uuid import uuid4


# Context variable for request correlation
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


def get_request_id() -> str:
    """Get the current request's correlation ID.
    
    Returns empty string if called outside a request context.
    """
    return request_id_var.get() or ""


def set_request_id(request_id: str | None = None) -> str:
    """Set a correlation ID for the current request context.
    
    Args:
        request_id: Optional explicit ID. If None, generates UUID4.
        
    Returns:
        The request ID that was set.
    """
    rid = request_id or str(uuid4())
    request_id_var.set(rid)
    return rid
