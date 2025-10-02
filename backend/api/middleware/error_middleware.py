"""
Error handling middleware for FastAPI.
Provides consistent error responses for Next.js frontend.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from typing import Union

from app.core import get_logger
from app.core.exceptions import ComplianceSystemException
from app.models import ErrorResponse, ErrorDetail

logger = get_logger(__name__)


def setup_error_handlers(app: FastAPI) -> None:
    """Setup error handlers for the FastAPI app."""
    
    @app.exception_handler(ComplianceSystemException)
    async def compliance_exception_handler(request: Request, exc: ComplianceSystemException):
        """Handle custom compliance system exceptions."""
        logger.error(f"Compliance system error: {exc.message}")
        
        error_response = ErrorResponse(
            error=ErrorDetail(
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details
            ),
            request_id=getattr(request.state, "request_id", None)
        )
        
        # Determine HTTP status code based on error type
        status_code = 500
        if exc.error_code in ["FILE_NOT_FOUND", "DOCUMENT_NOT_FOUND"]:
            status_code = 404
        elif exc.error_code in ["FILE_VALIDATION_ERROR", "INVALID_REQUEST"]:
            status_code = 400
        elif exc.error_code in ["AUTHENTICATION_ERROR"]:
            status_code = 401
        elif exc.error_code in ["AUTHORIZATION_ERROR"]:
            status_code = 403
        elif exc.error_code in ["EXTERNAL_SERVICE_ERROR"]:
            status_code = 503
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump(mode='json')
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        logger.warning(f"Validation error: {exc}")
        
        error_response = ErrorResponse(
            error=ErrorDetail(
                error_code="VALIDATION_ERROR",
                message="Request validation failed",
                details={
                    "errors": exc.errors(),
                    "body": exc.body if hasattr(exc, 'body') else None
                }
            ),
            request_id=getattr(request.state, "request_id", None)
        )
        
        return JSONResponse(
            status_code=422,
            content=error_response.model_dump(mode='json')
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions."""
        logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
        
        error_response = ErrorResponse(
            error=ErrorDetail(
                error_code=f"HTTP_{exc.status_code}",
                message=exc.detail,
                details={"status_code": exc.status_code}
            ),
            request_id=getattr(request.state, "request_id", None)
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(mode='json')
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions."""
        logger.warning(f"Starlette HTTP error {exc.status_code}: {exc.detail}")
        
        error_response = ErrorResponse(
            error=ErrorDetail(
                error_code=f"HTTP_{exc.status_code}",
                message=exc.detail,
                details={"status_code": exc.status_code}
            ),
            request_id=getattr(request.state, "request_id", None)
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(mode='json')
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        logger.error(f"Unexpected error: {exc}")
        logger.debug(traceback.format_exc())
        
        error_response = ErrorResponse(
            error=ErrorDetail(
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                details={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc) if not isinstance(exc, Exception) else "Internal server error"
                }
            ),
            request_id=getattr(request.state, "request_id", None)
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode='json')
        )