"""Prometheus metrics integration."""

from __future__ import annotations

import time
from typing import Callable

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response as StarletteResponse


REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests.",
    ("method", "path", "status"),
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ("method", "path"),
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to capture Prometheus metrics for each request."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], StarletteResponse]) -> StarletteResponse:
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.scope.get("route").path if request.scope.get("route") else request.url.path  # type: ignore[attr-defined]
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration = max(time.perf_counter() - start_time, 0.0)
            REQUEST_COUNTER.labels(method=method, path=path, status=str(status_code)).inc()
            REQUEST_LATENCY.labels(method=method, path=path).observe(duration)


def setup_metrics(app: FastAPI) -> None:
    """Register metrics middleware and /metrics endpoint."""

    if getattr(app.state, "metrics_configured", False):
        return

    app.add_middleware(MetricsMiddleware)

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint() -> Response:
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    app.state.metrics_configured = True




