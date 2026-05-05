from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

import app.db.models
import app.db.template_models  # noqa: F401
from app.core.config import get_settings

_engine: AsyncEngine | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            future=True,
        )
    return _engine


def set_engine(engine: AsyncEngine) -> None:
    """Replace the module-level engine (used by tests)."""
    global _engine
    _engine = engine


async def create_tables() -> None:
    """Create all SQLModel tables. Used for development and tests."""
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def dispose_engine() -> None:
    """Dispose the engine on shutdown to release connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for dependency injection."""
    engine = _get_engine()
    async with SQLModelAsyncSession(engine) as session:
        yield session
