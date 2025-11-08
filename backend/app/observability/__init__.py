"""Application observability initialisation."""

from __future__ import annotations

from fastapi import FastAPI

from app.core.config import get_settings
from app.observability.metrics import setup_metrics
from app.observability.request_id import RequestIDMiddleware
from app.observability.tracing import setup_tracing


def setup_observability(app: FastAPI) -> None:
    """Configure request id, metrics, and tracing for the FastAPI app."""

    if getattr(app.state, "observability_configured", False):
        return

    settings = get_settings()

    app.add_middleware(RequestIDMiddleware)

    if settings.metrics_enabled:
        setup_metrics(app)

    setup_tracing(app, settings=settings)

    app.state.observability_configured = True




