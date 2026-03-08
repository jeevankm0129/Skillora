import logging
from typing import AsyncGenerator

# UPGRADE: Import async_sessionmaker instead of the standard sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config import DATABASE_URL

logger = logging.getLogger(__name__)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in your .env file.")

# ===============================
# ENGINE & SESSION
# ===============================
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# FIXED: Native SQLAlchemy 2.0 async session factory.
# This completely resolves the __aenter__ and __init__ overload errors.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


# ===============================
# DEPENDENCY INJECTION
# ===============================
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide an async database session.
    Perfect for FastAPI routes or localized database calls.
    Ensures the session is safely closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
