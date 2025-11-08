"""OpenTelemetry tracing configuration and LangSmith integration."""

from __future__ import annotations

import os
from typing import Dict, Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import Settings


def _parse_headers(raw_headers: Optional[str]) -> Optional[Dict[str, str]]:
    if not raw_headers:
        return None
    headers: Dict[str, str] = {}
    for item in raw_headers.split(","):
        key, _, value = item.partition("=")
        if key and value:
            headers[key.strip()] = value.strip()
    return headers or None


def setup_tracing(app: FastAPI, *, settings: Settings) -> None:
    """Initialise OpenTelemetry tracing and LangSmith environment."""

    # Set LangSmith environment variables (use os.environ, not setdefault)
    # This ensures they're set even if already defined
    if settings.langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        if settings.langsmith_project:
            os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        
        # Log that LangSmith is enabled
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"LangSmith tracing enabled for project: {settings.langsmith_project}")

    if not settings.enable_tracing:
        return

    if getattr(app.state, "tracing_configured", False):
        return

    if not settings.otlp_endpoint:
        return

    resource = Resource.create(
        {
            "service.name": "python-research-portal",
            "service.namespace": "research-portal",
            "service.version": "0.1.0",
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=settings.otlp_endpoint,
        headers=_parse_headers(settings.otlp_headers),
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(tracer_provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider, excluded_urls="/metrics")
    RequestsInstrumentor().instrument()

    app.state.tracing_configured = True

