"""
Database models (ORM schema).

This module defines all database tables using SQLAlchemy ORM.
No business logic or queries are included here.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ---------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# ---------------------------------------------------------------------
# User
# ---------------------------------------------------------------------


class User(Base):
    """
    Application user.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    resumes: Mapped[List["Resume"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    job_preferences: Mapped[List["JobPreference"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notification_subscription: Mapped["NotificationSubscription"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------


class Resume(Base):
    """
    User resume (uploaded or generated).
    """

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="resumes")


# ---------------------------------------------------------------------
# Job Preference
# ---------------------------------------------------------------------


class JobPreference(Base):
    """
    User job preference settings.
    """

    __tablename__ = "job_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    preferred_location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    preferred_role: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="job_preferences")


# ---------------------------------------------------------------------
# Notification Subscription
# ---------------------------------------------------------------------


class NotificationSubscription(Base):
    """
    User notification subscription settings.
    """

    __tablename__ = "notification_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notification_subscription")


# ---------------------------------------------------------------------
# Job (cached job listings)
# ---------------------------------------------------------------------


class Job(Base):
    """
    Cached job listing fetched from external sources.
    """

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    # Comma-separated list of skills
    skills: Mapped[str] = mapped_column(Text, nullable=False)

    source: Mapped[str] = mapped_column(String(64), nullable=False)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
