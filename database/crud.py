import logging
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database import models

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

async def get_or_create_user_by_platform_id(
    db: AsyncSession,
    telegram_id: Optional[int] = None,
    whatsapp_id: Optional[str] = None,
) -> models.User:
    """
    Finds a user by platform ID, or creates a new one.
    Caller is responsible for committing the session.
    """
    if telegram_id is not None:
        stmt = select(models.User).where(models.User.telegram_id == telegram_id)
    elif whatsapp_id is not None:
        stmt = select(models.User).where(models.User.whatsapp_id == whatsapp_id)
    else:
        raise ValueError("Must provide either telegram_id or whatsapp_id.")

    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        user = models.User(telegram_id=telegram_id, whatsapp_id=whatsapp_id)
        db.add(user)
        await db.flush()       # Get the auto-generated ID immediately
        await db.refresh(user) # Ensure all server-side defaults are loaded

    return user


async def update_user_email(
    db: AsyncSession,
    email: str,
    telegram_id: Optional[int] = None,
    whatsapp_id: Optional[str] = None,
) -> models.User:
    """Updates a user's email and enables email notifications."""
    user = await get_or_create_user_by_platform_id(db, telegram_id, whatsapp_id)
    user.email = email
    user.notify_by_email = True
    await db.flush()
    return user


async def enable_background_tracking(
    db: AsyncSession,
    telegram_id: Optional[int] = None,
    whatsapp_id: Optional[str] = None,
) -> models.User:
    """Enables the background job-hunt scheduler for a user."""
    user = await get_or_create_user_by_platform_id(db, telegram_id, whatsapp_id)
    user.background_tracking_enabled = True
    await db.flush()
    return user


async def save_resume_text(
    db: AsyncSession,
    text_content: str,
    telegram_id: Optional[int] = None,
    whatsapp_id: Optional[str] = None,
) -> models.Resume:
    """
    Inserts or updates the resume text for a user.
    Uses upsert logic: updates existing record, creates new one if absent.
    """
    user = await get_or_create_user_by_platform_id(db, telegram_id, whatsapp_id)

    stmt = select(models.Resume).where(models.Resume.user_id == user.id)
    result = await db.execute(stmt)
    resume = result.scalars().first()

    if resume:
        resume.text_content = text_content
    else:
        resume = models.Resume(user_id=user.id, text_content=text_content)
        db.add(resume)

    await db.flush()
    await db.refresh(resume)  # FIX: ensure auto-generated fields (id, etc.) are populated
    return resume


# ---------------------------------------------------------------------------
# Atomic helper for the Telegram job-recommendation flow
# ---------------------------------------------------------------------------

async def save_user_resume_and_activate(
    db: AsyncSession,
    email: str,
    resume_text: str,
    telegram_id: Optional[int] = None,
    whatsapp_id: Optional[str] = None,
) -> models.User:
    """
    Single atomic operation that:
      1. Gets or creates the user
      2. Saves their email + enables email notifications
      3. Saves resume text (upsert)
      4. Enables background tracking

    The caller (via get_db_context) commits the transaction.
    If any step fails, the entire operation is rolled back.
    """
    user = await get_or_create_user_by_platform_id(db, telegram_id, whatsapp_id)

    user.email = email
    user.notify_by_email = True
    user.background_tracking_enabled = True
    await db.flush()

    # Resume upsert
    stmt = select(models.Resume).where(models.Resume.user_id == user.id)
    result = await db.execute(stmt)
    resume = result.scalars().first()

    if resume:
        resume.text_content = resume_text
    else:
        resume = models.Resume(user_id=user.id, text_content=resume_text)
        db.add(resume)

    await db.flush()
    await db.refresh(resume)
    await db.refresh(user)

    logger.info(f"User {user.id} activated with email and background tracking.")
    return user


# ---------------------------------------------------------------------------
# Background scheduler queries
# ---------------------------------------------------------------------------

async def get_users_for_background_check(
    db: AsyncSession,
) -> Sequence[models.User]:
    """
    Returns all users with background tracking enabled,
    eagerly loading their resume and existing job matches.
    """
    stmt = (
        select(models.User)
        .options(
            selectinload(models.User.resume),
            selectinload(models.User.job_matches).selectinload(
                models.UserJobMatch.job
            ),
        )
        .where(models.User.background_tracking_enabled == True)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
