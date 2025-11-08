"""Structured logging setup using structlog."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from opentelemetry import trace


def configure_logging(level: str = "INFO") -> None:
    """Configure stdlib logging and structlog processors."""

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        add_trace_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.dev.ConsoleRenderer()
            if level.upper() == "DEBUG"
            else structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )


def get_logger(name: str, **initial_values: Any) -> structlog.stdlib.BoundLogger:
    """Return a structured logger bound with initial context."""

    return structlog.get_logger(name).bind(**initial_values)


def add_trace_context(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Inject OpenTelemetry trace and span identifiers into log events."""

    span = trace.get_current_span()
    if not span:
        return event_dict
    context = span.get_span_context()
    if not context.is_valid:
        return event_dict
    event_dict["trace_id"] = format(context.trace_id, "032x")
    event_dict["span_id"] = format(context.span_id, "016x")
    return event_dict

