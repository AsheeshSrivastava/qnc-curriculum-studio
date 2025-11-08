"""Database engine and session management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _build_async_url(raw_url: str) -> str:
    if "+psycopg_async" in raw_url:
        return raw_url
    if "+psycopg://" in raw_url:
        return raw_url.replace("+psycopg://", "+psycopg_async://", 1)
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg_async://", 1)
    raise ValueError("Unsupported database driver for async engine.")


class Database:
    """Singleton-style database registry for async/sync engines."""

    def __init__(self) -> None:
        self._async_engine: Optional[AsyncEngine] = None
        self._sync_engine: Optional[Engine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def configure(self) -> None:
        settings = get_settings()
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL must be set to initialize the database.")

        async_url = _build_async_url(str(settings.database_url))
        self._async_engine = create_async_engine(
            async_url,
            echo=settings.app_env == "development",
            pool_pre_ping=True,
        )
        self._session_factory = async_sessionmaker(
            self._async_engine,
            expire_on_commit=False,
        )

        self._sync_engine = create_engine(
            str(settings.database_url),
            pool_pre_ping=True,
        )

        logger.info("database.configured", async_url=async_url)

    @property
    def async_engine(self) -> AsyncEngine:
        if self._async_engine is None:
            self.configure()
        return self._async_engine  # type: ignore[return-value]

    @property
    def sync_engine(self) -> Engine:
        if self._sync_engine is None:
            self.configure()
        return self._sync_engine  # type: ignore[return-value]

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self.configure()
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        session_factory = self.session_factory
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


database = Database()

