from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import uvicorn
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import compliance engine
try:
    from updated_compliance_system import RuleBasedComplianceEngine
    compliance_engine = RuleBasedComplianceEngine()
    logger = logging.getLogger(__name__)
    logger.info("Compliance engine initialized successfully")
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to initialize compliance engine: {e}")
    compliance_engine = None

from .routes import documents, compliance
from .models.schemas import HealthCheckResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Insurance Compliance System API",
    description="AI-powered insurance compliance monitoring and analysis system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(compliance.router)

@app.get("/", response_model=HealthCheckResponse)
async def root():
    """Root endpoint with health check"""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        services={
            "api": "running",
            "database": "connected",  # TODO: Check actual database
            "ml_models": "loaded",    # TODO: Check model availability
            "ollama": "available"     # TODO: Check Ollama service
        },
        timestamp=datetime.utcnow()
    )

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Detailed health check endpoint"""
    try:
        services = {
            "api": "running",
            "database": "connected",  # Mock - could add real DB check
            "storage": "accessible",
        }
        
        # Check compliance engine
        if compliance_engine:
            services["compliance_engine"] = "loaded"
        else:
            services["compliance_engine"] = "error"
        
        # Check if Legal BERT model is available
        try:
            model_path = project_root / "models" / "legal_bert_rule_classification"
            if model_path.exists():
                services["legal_bert"] = "loaded"
            else:
                services["legal_bert"] = "not_found"
        except:
            services["legal_bert"] = "error"
        
        # Determine overall status
        status = "healthy" if all(s in ["running", "connected", "loaded", "accessible"] for s in services.values()) else "degraded"
        
        return HealthCheckResponse(
            status=status,
            version="1.0.0",
            services=services,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error="SERVICE_UNAVAILABLE",
                message="One or more services are unhealthy",
                details={"exception": str(e)},
                timestamp=datetime.utcnow()
            ).dict()
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail,
            timestamp=datetime.utcnow()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={"exception": str(exc)},
            timestamp=datetime.utcnow()
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )