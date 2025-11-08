"""FastAPI application entrypoint."""

# CRITICAL: Fix Windows async event loop BEFORE any other imports
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Now safe to import everything else
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.redis import init_redis
from app.db.utils import init_db
from app.observability import setup_observability

# Initialize LangSmith tracing BEFORE any LangChain imports
# This must happen early to ensure all LangChain/LangGraph calls are traced
_settings = get_settings()
if _settings.langsmith_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = _settings.langsmith_api_key
    if _settings.langsmith_project:
        os.environ["LANGCHAIN_PROJECT"] = _settings.langsmith_project
    print(f"[LangSmith] Tracing enabled for project: {_settings.langsmith_project}")


def create_application() -> FastAPI:
    """Instantiate FastAPI application with routers and middleware."""

    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__, app_env=settings.app_env)

    app = FastAPI(
        title="Python Research Portal API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    setup_observability(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_db()
        await init_redis()
        logger.info("startup.complete")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("shutdown.complete")

    app.state.settings = settings

    return app


app = create_application()

