from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from app.core.config import get_settings

_engine = create_async_engine(
    get_settings().database_url,
    echo=get_settings().debug,
    future=True,
)


async def create_tables() -> None:
    """Create all SQLModel tables. Used for development and tests."""
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for dependency injection."""
    async with SQLModelAsyncSession(_engine) as session:
        yield session
