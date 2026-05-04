"""
FastAPI application factory and main entry point.
Next.js compatible API with proper CORS and error handling.
"""

from contextlib import asynccontextmanager
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
import time
from datetime import datetime

from app.core import settings, get_logger
from app.core.exceptions import ComplianceSystemException
from app.services.compliance_service import ComplianceService
from .v1.router import api_router
from .middleware.error_middleware import setup_error_handlers
from .dependencies import set_compliance_service, get_compliance_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Insurance Compliance System API...")
    try:
        compliance_service = ComplianceService()
        await compliance_service.initialize()
        set_compliance_service(compliance_service)
        logger.info("API startup completed successfully")
    except Exception as e:
        logger.error(f"API startup failed: {e}")
        raise
    
    # Phase 1: Start scheduler for automated scraping
    scheduler = None
    try:
        from app.services.scheduler import SchedulerService
        from api.v1.endpoints.scraper_admin import set_scheduler_service
        scheduler = SchedulerService()
        await scheduler.start()
        set_scheduler_service(scheduler)
    except Exception as e:
        logger.warning(f"⚠️ Scheduler startup failed (scraping disabled): {e}")
    
    yield
    
    # Shutdown
    if scheduler:
        await scheduler.shutdown()
    logger.info("Shutting down API...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI app instance
    """
    
    # Create FastAPI app with lifespan management
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered insurance compliance monitoring and analysis system",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # CORS middleware for Next.js frontend (must be outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )
    
    # Phase 4: Rate limiting middleware (after CORS)
    from .middleware.rate_limiter import RateLimiterMiddleware
    app.add_middleware(
        RateLimiterMiddleware,
        max_requests=settings.RATE_LIMIT_MAX,
        window_seconds=settings.RATE_LIMIT_WINDOW,
    )
    
    # Phase 4: Optional API key authentication (after rate limiter)
    from .middleware.auth_middleware import APIKeyMiddleware
    api_keys = None
    if settings.API_KEYS:
        api_keys = {k.strip() for k in settings.API_KEYS.split(",") if k.strip()}
    app.add_middleware(APIKeyMiddleware, api_keys=api_keys or None)
    
    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Request ID middleware (Phase 6: UUID4 correlation IDs via contextvars)
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        from app.core.context import set_request_id
        request_id = set_request_id()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_PREFIX)
    
    # Health check endpoint (outside versioned API)
    @app.get("/health")
    async def health_check():
        """Health check endpoint for load balancers."""
        try:
            service = get_compliance_service()
            engine_status = "healthy" if service.is_initialized() else "unhealthy"
        except HTTPException:
            engine_status = "unhealthy"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "services": {
                "compliance_engine": engine_status
            }
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health",
            "api": settings.API_PREFIX
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )