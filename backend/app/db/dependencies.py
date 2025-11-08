"""FastAPI dependencies for database access."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import database


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with database.session() as session:
        yield session

