"""
app/core/logging.py

Configures structlog for structured JSON logging.
Every log entry automatically includes timestamp, level, logger name,
and any context bound via structlog.contextvars (e.g. request_id).
"""
import logging
import sys
import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Call once at application startup."""

    # Route stdlib logging through structlog so SQLAlchemy / uvicorn
    # logs also get structured.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    return structlog.get_logger(name)
