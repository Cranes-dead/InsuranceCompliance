"""
Middleware package initialization
"""
from .error_middleware import setup_error_handlers

__all__ = ["setup_error_handlers"]