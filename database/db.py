import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config import DATABASE_URL

logger = logging.getLogger(__name__)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in your .env file.")

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    # check_same_thread is SQLite-only; ignored by asyncpg
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency — yields a session for route-level injection
# ---------------------------------------------------------------------------
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Use this ONLY as a FastAPI dependency via Depends().
    For bot handlers and background tasks use get_db_context() below.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"DB session error (FastAPI): {e}", exc_info=True)
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# General-purpose async context manager
# ---------------------------------------------------------------------------
@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Proper async context manager for use in Telegram bot handlers,
    background tasks, and anywhere that is NOT a FastAPI route.

    Usage:
        async with get_db_context() as db:
            await crud.some_operation(db, ...)

    Guarantees rollback on exception and always closes the session.
    Replaces the previous anti-pattern:
        async for db in get_db_session():
            ...
            break
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"DB session error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()
