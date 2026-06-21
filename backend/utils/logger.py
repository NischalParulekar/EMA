"""Logging helper for EMA.

main.py configures the root logger via logging.basicConfig(level=settings.log_level).
Use get_logger(__name__) in modules that want a named child logger.
"""
import logging
from backend.config import settings


def get_logger(name: str) -> logging.Logger:
    """Return a named logger configured at the app's LOG_LEVEL."""
    logger = logging.getLogger(name)
    logger.setLevel(settings.log_level)
    return logger
