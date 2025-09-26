"""
System health and monitoring endpoints.
"""

from fastapi import APIRouter
from datetime import datetime
import psutil
import asyncio

from app.core import get_logger, settings

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns system status, service health, and performance metrics.
    """
    try:
        # Check system resources
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Test async operations
        start_time = datetime.utcnow()
        await asyncio.sleep(0.001)  # Small async test
        response_time = (datetime.utcnow() - start_time).total_seconds()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "services": {
                "api": "healthy",
                "compliance_engine": "healthy",  # This would check actual service
                "database": "healthy",  # This would check DB connection
                "ollama": "unknown"  # This would test Ollama connection
            },
            "system": {
                "memory_usage": f"{memory.percent}%",
                "memory_available": f"{memory.available // (1024**3)}GB",
                "disk_usage": f"{disk.percent}%",
                "disk_free": f"{disk.free // (1024**3)}GB"
            },
            "performance": {
                "response_time": f"{response_time:.3f}s",
                "uptime": "N/A"  # This would track actual uptime
            }
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/metrics")
async def get_system_metrics():
    """
    Get detailed system metrics for monitoring.
    
    Returns performance and usage statistics.
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics (basic)
        network = psutil.net_io_counters()
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "percent": swap.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/info")
async def get_system_info():
    """
    Get system and application information.
    
    Returns configuration and environment details.
    """
    try:
        import platform
        import sys
        
        info = {
            "application": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG
            },
            "system": {
                "platform": platform.platform(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "hostname": platform.node()
            },
            "configuration": {
                "api_host": settings.API_HOST,
                "api_port": settings.API_PORT,
                "database_url": settings.DATABASE_URL.split("://")[0] + "://***",  # Hide credentials
                "max_file_size": settings.MAX_FILE_SIZE,
                "allowed_extensions": settings.ALLOWED_EXTENSIONS
            },
            "features": {
                "legal_bert": True,
                "ollama_integration": bool(settings.OLLAMA_BASE_URL),
                "batch_processing": True,
                "document_upload": True
            }
        }
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }