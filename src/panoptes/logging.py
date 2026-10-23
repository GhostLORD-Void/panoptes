"""Structured logging setup for development and production runs."""

from __future__ import annotations

import logging
from typing import Any

import structlog


def configure_logging(*, mode: str = "dev", level: str = "INFO") -> None:
    """Configure pretty development output or production JSON."""
    normalized_mode = mode.lower()
    if normalized_mode not in {"dev", "prod"}:
        raise ValueError("mode must be 'dev' or 'prod'")
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Unknown logging level: {level}")
    logging.basicConfig(level=numeric_level, format="%(message)s", force=True)
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    processors.append(
        structlog.processors.JSONRenderer()
        if normalized_mode == "prod"
        else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )


def bind_run_context(*, run_id: str, target: str) -> None:
    """Bind run identifiers to log events in the current context."""
    structlog.contextvars.bind_contextvars(run_id=run_id, target=target)


def clear_run_context() -> None:
    """Clear context to prevent fields leaking between runs."""
    structlog.contextvars.clear_contextvars()
