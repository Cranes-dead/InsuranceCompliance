"""
Logging configuration for the Insurance Compliance System.

Phase 6: Enhanced with structured JSON logging and request correlation IDs.
- Development: human-readable text format
- Production/Staging: structured JSON format for log aggregation (ELK, Datadog, etc.)
- All environments: request_id injected into every log record via RequestIdFilter
"""

import json
import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any

from .config import settings


class RequestIdFilter(logging.Filter):
    """Injects request_id from contextvars into every log record.
    
    Uses lazy import to avoid circular dependency:
    context.py → (nothing) ← logging.py (lazy import in filter)
    """
    
    def filter(self, record):
        # Lazy import avoids circular: logging.py is imported by __init__.py
        # which is imported before context.py would be available at module level
        from app.core.context import get_request_id
        record.request_id = get_request_id()
        return True


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production/staging environments.
    
    Outputs one JSON object per line — compatible with log aggregation tools
    like ELK Stack, Datadog, CloudWatch, and GCP Logging.
    """
    
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", ""),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)


# Shared filter instance
_request_id_filter = RequestIdFilter()

# Determine formatter based on environment
_is_production = settings.ENVIRONMENT in ("production", "staging")


def setup_logging() -> None:
    """Setup logging configuration with request correlation and conditional JSON output."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Logging configuration dictionary
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(module)s - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": log_dir / "compliance_system.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed", 
                "filename": log_dir / "errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file"],
        },
    }
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Add RequestIdFilter to all handlers so %(request_id)s is always available
    for handler_name in logging_config["handlers"]:
        handler = logging.getLogger().handlers
        # Apply to root logger handlers
    
    # Apply filter to all existing handlers across all loggers
    _apply_request_id_filter()
    
    # In production/staging, swap console handler to JSON formatter
    if _is_production:
        _apply_json_console_formatter()
    
    # Set specific logger levels for third-party libraries
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("sklearn").setLevel(logging.WARNING)
    # Suppress httpx/httpcore — they log every Supabase request URL at INFO level,
    # which leaks the Supabase project URL into logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def _apply_request_id_filter() -> None:
    """Apply RequestIdFilter to all handlers across all loggers."""
    # Root logger
    for handler in logging.getLogger().handlers:
        handler.addFilter(_request_id_filter)
    
    # Named loggers
    for logger_name in ("app", "uvicorn", "uvicorn.error", "uvicorn.access"):
        for handler in logging.getLogger(logger_name).handlers:
            handler.addFilter(_request_id_filter)


def _apply_json_console_formatter() -> None:
    """Replace console handler formatter with JSONFormatter for production."""
    json_formatter = JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setFormatter(json_formatter)
    
    for logger_name in ("app", "uvicorn", "uvicorn.error", "uvicorn.access"):
        for handler in logging.getLogger(logger_name).handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setFormatter(json_formatter)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(f"app.{name}")


# Setup logging when module is imported
setup_logging()