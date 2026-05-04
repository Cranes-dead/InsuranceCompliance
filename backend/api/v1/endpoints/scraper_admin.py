"""
Admin endpoints for scraper management.

Phase 1: Provides manual trigger, status, and history endpoints
for the regulation scraper. Should be protected by API key auth
(Phase 4) in production.
"""

from fastapi import APIRouter
from typing import Optional

from app.core import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Global reference set during lifespan startup
_scheduler_service = None


def set_scheduler_service(service) -> None:
    """Set the global scheduler service reference.
    
    Called from api/main.py lifespan during startup.
    """
    global _scheduler_service
    _scheduler_service = service


@router.post("/scraper/trigger")
async def trigger_scrape(force: bool = False):
    """Manually trigger a regulation scrape.
    
    Args:
        force: If True, run even if recently completed.
    
    Returns:
        Scrape result with status and statistics.
    """
    if _scheduler_service is None:
        return {"error": "Scheduler not initialized", "status": "unavailable"}
    
    logger.info("🔧 Manual scrape triggered via admin API")
    result = await _scheduler_service.scraper_service.run_scrape(force=force)
    return result


@router.get("/scraper/status")
async def scraper_status():
    """Get current scraper status.
    
    Returns:
        Current running state, last run time, and last result.
    """
    if _scheduler_service is None:
        return {"error": "Scheduler not initialized", "status": "unavailable"}
    
    return _scheduler_service.scraper_service.status


@router.get("/scraper/history")
async def scraper_history(limit: int = 10):
    """Get recent scrape run history.
    
    Args:
        limit: Maximum number of history entries to return (default 10).
    
    Returns:
        List of recent scrape runs with timestamps and results.
    """
    if _scheduler_service is None:
        return {"error": "Scheduler not initialized", "status": "unavailable"}
    
    history = _scheduler_service.scraper_service._run_history
    return {"runs": history[-limit:], "total": len(history)}
