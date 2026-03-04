"""
Sports AI — Structured Logger
JSON-formatted logging for production, colored for development.
"""

import logging
import sys
import json
from datetime import datetime, timezone
from backend.config.settings import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production environments."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")
        return (
            f"{self.BOLD}{color}[{timestamp}] "
            f"{record.levelname:8s}{self.RESET} "
            f"\033[90m{record.module}.{record.funcName}\033[0m → "
            f"{record.getMessage()}"
        )


def get_logger(name: str) -> logging.Logger:
    """
    Create a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(f"sports_ai.{name}")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        if settings.is_production:
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(ColoredFormatter())

        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.propagate = False

    return logger
