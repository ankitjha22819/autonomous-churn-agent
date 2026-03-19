"""
Structured logging configuration using structlog.

Provides consistent, parseable logs across the application.
JSON format in production, colored console output in development.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from churn_agent.core.config import get_settings


def setup_logging() -> None:
    """
    Configure structlog with environment-appropriate processors.
    
    Call this once at application startup.
    """
    settings = get_settings()
    
    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    if settings.log_format == "json":
        # Production: JSON logs for log aggregators (Datadog, ELK, etc.)
        shared_processors.extend([
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ])
    else:
        # Development: Pretty console output
        shared_processors.extend([
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ])
    
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(settings.log_level),
    )
    
    # Quiet noisy third-party loggers
    for logger_name in ["httpx", "httpcore", "uvicorn.access"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str | None = None, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        **initial_context: Key-value pairs to bind to all log entries
        
    Returns:
        A bound structlog logger
        
    Usage:
        logger = get_logger(__name__, job_id="abc123")
        logger.info("Processing started", customer_id=42)
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


class LogContext:
    """
    Context manager for temporary log context binding.
    
    Usage:
        with LogContext(request_id="req-123", user_id=42):
            logger.info("Processing request")  # Includes request_id and user_id
    """
    
    def __init__(self, **context: Any) -> None:
        self.context = context
        self._token: Any = None
    
    def __enter__(self) -> "LogContext":
        self._token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, *args: Any) -> None:
        structlog.contextvars.unbind_contextvars(*self.context.keys())