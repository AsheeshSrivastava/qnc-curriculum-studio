"""Database utility helpers."""

from __future__ import annotations

from sqlalchemy import text

from app.core.logging import get_logger
from app.db.base import metadata
from app.db.session import database

logger = get_logger(__name__)


async def init_db() -> None:
    """Ensure database connectivity and required schema."""

    database.configure()
    async_engine = database.async_engine

    async with async_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(metadata.create_all)

    logger.info("database.initialized")

