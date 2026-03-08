from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base

# Association table for Many-to-Many User <-> Skill relationship
user_skill_association = Table(
    "user_skill",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, unique=True, index=True, nullable=True
    )
    whatsapp_id: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)

    # Notification Flags
    notify_by_email: Mapped[bool] = mapped_column(Boolean, default=False)
    background_tracking_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    resume: Mapped[Optional["Resume"]] = relationship(
        "Resume", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    skills: Mapped[List["Skill"]] = relationship(
        "Skill", secondary=user_skill_association, back_populates="users"
    )
    job_matches: Mapped[List["UserJobMatch"]] = relationship(
        "UserJobMatch", back_populates="user", cascade="all, delete-orphan"
    )


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    text_content: Mapped[str] = mapped_column(Text, nullable=False)

    # We will store the generated ATS PDF path here later
    pdf_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="resume")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    users: Mapped[List["User"]] = relationship(
        "User", secondary=user_skill_association, back_populates="skills"
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    company: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    link: Mapped[str] = mapped_column(String, unique=True)
    source: Mapped[str] = mapped_column(String, default="API")

    # Crucial for the background loop
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    matches: Mapped[List["UserJobMatch"]] = relationship(
        "UserJobMatch", back_populates="job", cascade="all, delete-orphan"
    )


class UserJobMatch(Base):
    __tablename__ = "user_job_matches"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_user_job"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))

    relevance_score: Mapped[int] = mapped_column(Integer, default=0)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="job_matches")
    job: Mapped["Job"] = relationship("Job", back_populates="matches")
