from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database import models


# FIXED: Added Optional to allow None values without angering the type checker
async def get_or_create_user_by_platform_id(
    db: AsyncSession, telegram_id: Optional[int] = None, whatsapp_id: Optional[str] = None
) -> models.User:
    """Finds a user by their platform ID, or creates them if they don't exist."""

    # Explicitly check for None to make the linter happy
    if telegram_id is not None:
        stmt = select(models.User).where(models.User.telegram_id == telegram_id)
    elif whatsapp_id is not None:
        stmt = select(models.User).where(models.User.whatsapp_id == whatsapp_id)
    else:
        raise ValueError("Must provide either telegram_id or whatsapp_id")

    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        user = models.User(telegram_id=telegram_id, whatsapp_id=whatsapp_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def update_user_email(
    db: AsyncSession,
    email: str,
    telegram_id: Optional[int] = None,
    whatsapp_id: Optional[str] = None,
):
    user = await get_or_create_user_by_platform_id(db, telegram_id, whatsapp_id)
    user.email = email
    user.notify_by_email = True
    await db.commit()


async def enable_background_tracking(
    db: AsyncSession, telegram_id: Optional[int] = None, whatsapp_id: Optional[str] = None
):
    user = await get_or_create_user_by_platform_id(db, telegram_id, whatsapp_id)
    user.background_tracking_enabled = True
    await db.commit()


async def save_resume_text(
    db: AsyncSession,
    text_content: str,
    telegram_id: Optional[int] = None,
    whatsapp_id: Optional[str] = None,
):
    user = await get_or_create_user_by_platform_id(db, telegram_id, whatsapp_id)

    stmt = select(models.Resume).where(models.Resume.user_id == user.id)
    result = await db.execute(stmt)
    resume = result.scalars().first()

    if resume:
        resume.text_content = text_content
    else:
        resume = models.Resume(user_id=user.id, text_content=text_content)
        db.add(resume)

    await db.commit()


# FIXED: Changed the return type hint to Sequence to match SQLAlchemy's output
async def get_users_for_background_check(db: AsyncSession) -> Sequence[models.User]:
    """Fetches users who are actively looking for jobs."""
    stmt = (
        select(models.User)
        .options(selectinload(models.User.resume))
        .where(models.User.background_tracking_enabled == True)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
