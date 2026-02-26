from __future__ import annotations

from sqlalchemy import Column  # Required for Table definitions
from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from database.db import Base

from sqlalchemy import UniqueConstraint

# Many-to-Many: Users <-> Skills
# FIX: Use standard 'Column' for Table definitions, not 'mapped_column'
user_skill_association = Table(
    "user_skill",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("skill_id", Integer, ForeignKey("skills.id")),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    whatsapp_id: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)

    notify_by_email: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_by_telegram: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    resume: Mapped[Resume | None] = relationship(
        "Resume", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    skills: Mapped[list[Skill]] = relationship(
        "Skill", secondary=user_skill_association, back_populates="users"
    )
    job_matches: Mapped[list[UserJobMatch]] = relationship(
        "UserJobMatch", back_populates="user", cascade="all, delete-orphan"
    )


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    text_content: Mapped[str] = mapped_column(Text, nullable=False)

    parsed_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="resume")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    users: Mapped[list[User]] = relationship(
        "User", secondary=user_skill_association, back_populates="skills"
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    company: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    link: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String, default="Manual")

    matches: Mapped[list[UserJobMatch]] = relationship("UserJobMatch", back_populates="job")


class UserJobMatch(Base):
    __tablename__ = "user_job_matches"

    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_user_job"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"))

    relevance_score: Mapped[int] = mapped_column(Integer, default=0)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    notified: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship("User", back_populates="job_matches")
    job: Mapped[Job] = relationship("Job", back_populates="matches")
