"""
CRUD operations for the database.

This module contains all database access logic.
No business logic should be written here.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.database.models import Job, Resume, User


# ---------------------------------------------------------------------
# User operations
# ---------------------------------------------------------------------


def get_user_by_telegram_id(
    session: Session,
    telegram_user_id: str,
) -> User | None:
    """
    Fetch a user by Telegram user ID.
    """
    return (
        session.query(User)
        .filter(User.telegram_user_id == telegram_user_id)
        .one_or_none()
    )


def create_user(
    session: Session,
    telegram_user_id: str,
) -> User:
    """
    Create a new user with the given Telegram user ID.
    """
    user = User(telegram_user_id=telegram_user_id)
    session.add(user)
    session.flush()  # Ensures user.id is generated
    return user


# ---------------------------------------------------------------------
# Resume operations
# ---------------------------------------------------------------------


def save_resume(
    session: Session,
    user_id: int,
    resume_text: str,
) -> Resume:
    """
    Save resume text for a user.
    """
    resume = Resume(
        user_id=user_id,
        content=resume_text,
    )
    session.add(resume)
    session.flush()
    return resume


# ---------------------------------------------------------------------
# Job cache operations
# ---------------------------------------------------------------------


def get_cached_jobs(
    session: Session,
    max_age_minutes: int = 60,
) -> List[Job]:
    """
    Fetch recently cached jobs from the database.
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)

    return (
        session.query(Job)
        .filter(Job.fetched_at >= cutoff_time)
        .all()
    )


def save_jobs(
    session: Session,
    jobs: List[dict],
    source: str,
) -> None:
    """
    Save job listings to the database.
    """
    for job in jobs:
        job_obj = Job(
            title=job["title"],
            location=job["location"],
            skills=",".join(job["required_skills"]),
            source=source,
        )
        session.add(job_obj)
