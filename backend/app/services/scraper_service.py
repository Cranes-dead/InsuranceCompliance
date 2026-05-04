"""
Async wrapper around the existing scraper with concurrency protection.

Phase 1: Wraps the synchronous SmartMotorVehicleScraper in asyncio.to_thread()
with an asyncio.Lock() to prevent concurrent scrape runs. Tracks run history
with bounded storage (last 50 runs).
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.core import get_logger

logger = get_logger(__name__)


class ScraperService:
    """Async scraper service with concurrency lock and run history.
    
    The underlying scraper (smart_scraper.py) is synchronous and uses
    Selenium WebDriver, so all scrape calls are wrapped in
    asyncio.to_thread() to avoid blocking the event loop.
    """
    
    def __init__(self):
        self._last_run: Optional[datetime] = None
        self._last_result: Optional[Dict[str, Any]] = None
        self._is_running: bool = False
        self._lock = asyncio.Lock()
        self._run_history: List[Dict[str, Any]] = []
        self._max_history: int = 50
    
    @property
    def status(self) -> Dict[str, Any]:
        """Get current scraper status."""
        return {
            "is_running": self._is_running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "last_result": self._last_result,
            "total_runs": len(self._run_history),
        }
    
    async def run_scrape(self, force: bool = False) -> Dict[str, Any]:
        """Run a scrape with concurrency protection.
        
        Args:
            force: If True, run even if recently completed.
            
        Returns:
            Dict with status, counts, and any errors.
        """
        # Quick check (non-blocking) — if already running, reject
        if self._is_running:
            return {
                "status": "already_running",
                "message": "A scrape is already in progress. Check /scraper/status for details.",
            }
        
        # Acquire lock to set the running flag atomically
        async with self._lock:
            if self._is_running:
                return {"status": "already_running", "message": "Race condition avoided."}
            self._is_running = True
        
        try:
            logger.info("🕷️ Starting scheduled regulation scrape...")
            start_time = datetime.utcnow()
            
            # Run the sync scraper in a thread so we don't block the event loop
            result = await asyncio.to_thread(self._execute_scrape)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            self._last_run = end_time
            self._last_result = {**result, "duration_seconds": round(duration, 1)}
            
            # Append to bounded history
            self._run_history.append({
                "timestamp": end_time.isoformat(),
                "duration_seconds": round(duration, 1),
                "result": result,
            })
            if len(self._run_history) > self._max_history:
                self._run_history = self._run_history[-self._max_history:]
            
            logger.info(f"✅ Scrape completed in {duration:.1f}s: {result}")
            return self._last_result
            
        except Exception as e:
            logger.error(f"❌ Scrape failed: {e}")
            error_result = {"status": "failed", "error": str(e)}
            self._last_result = error_result
            return error_result
            
        finally:
            self._is_running = False
    
    def _execute_scrape(self) -> Dict[str, Any]:
        """Synchronous scrape execution (runs inside asyncio.to_thread).
        
        Imports and runs the SmartMotorVehicleScraper. This is the only
        place that touches the scraper code, keeping the boundary clean.
        """
        try:
            # Import here to avoid loading heavy Selenium/torch deps at server start
            from smart_scraper import SmartMotorVehicleScraper
            
            scraper = SmartMotorVehicleScraper()
            scraper.run()
            
            # Extract stats from the scraper instance
            stats = scraper.enhanced_stats
            return {
                "status": "success",
                "total_links_found": stats.get("total_links_found", 0),
                "successfully_downloaded": stats.get("successfully_downloaded", 0),
                "filtered_by_url": stats.get("filtered_by_url", 0),
                "filtered_by_link_text": stats.get("filtered_by_link_text", 0),
                "filtered_by_blacklist": stats.get("filtered_by_blacklist", 0),
                "filtered_by_metadata": stats.get("filtered_by_metadata", 0),
                "filtered_by_bert": stats.get("filtered_by_bert", 0),
            }
            
        except ImportError as e:
            logger.error(f"Scraper import failed (missing dependencies?): {e}")
            return {
                "status": "error",
                "error": f"Scraper not available: {e}",
                "message": "Ensure scraper dependencies (selenium, webdriver-manager) are installed.",
            }
        except Exception as e:
            logger.error(f"Scraper execution error: {e}")
            return {"status": "error", "error": str(e)}
