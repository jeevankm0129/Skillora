"""
Database initialization module.

Responsibilities:
- Create SQLAlchemy engine
- Support SQLite and PostgreSQL
- Provide a transactional session factory

No models or queries are defined here.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseError(Exception):
    """Raised when database initialization fails."""


settings = Settings()

if not settings.DATABASE_URL:
    raise DatabaseError("DATABASE_URL is not configured")

# ✅ Engine is defined at module level (important)
engine: Engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

logger.info("Database engine initialized")


@contextmanager
def get_session() -> Iterator[Session]:
    """
    Provide a transactional database session.

    Usage:
        with get_session() as session:
            ...
    """
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
