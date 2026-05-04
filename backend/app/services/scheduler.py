"""
APScheduler lifecycle management for scheduled tasks.

Phase 1: Manages an AsyncIOScheduler with a daily cron job for
regulation scraping. Integrates with FastAPI lifespan for clean
startup/shutdown.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core import get_logger
from app.services.scraper_service import ScraperService

logger = get_logger(__name__)


class SchedulerService:
    """APScheduler service managing scheduled regulation scrapes.
    
    Usage in FastAPI lifespan:
        scheduler = SchedulerService()
        await scheduler.start()
        yield
        await scheduler.shutdown()
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scraper_service = ScraperService()
    
    async def start(self) -> None:
        """Start the scheduler with configured jobs."""
        self.scheduler.add_job(
            self.scraper_service.run_scrape,
            CronTrigger(hour=2, minute=0),  # 2:00 AM daily
            id="daily_regulation_scrape",
            name="Daily IRDAI Regulation Scrape",
            replace_existing=True,
            misfire_grace_time=3600,  # Allow 1hr late execution if server was down
        )
        self.scheduler.start()
        logger.info("📅 Scheduler started — daily regulation scrape at 02:00 AM")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("📅 Scheduler stopped")
