import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import ENABLE_EMAIL_NOTIFICATIONS
from database import crud, models
from database.db import SessionLocal
from services.ai_service import get_job_recommendations
from utils.email_sender import send_email

logger = logging.getLogger(__name__)

_scheduler = None  # Prevent duplicate schedulers


async def process_user_notifications(user_id: int):
    """
    Safely process job notifications for ONE user.
    """
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user or not user.resume:
            return

        resume_text = user.resume.text_content
        if not resume_text:
            return

        # 1. Ask AI for job recommendations (AI handles skills + ranking)
        try:
            ranked_jobs = await get_job_recommendations(
                skills=[],
                resume_text=resume_text,
            )
        except Exception as e:
            logger.error(f"AI job recommendation failed for user {user.id}: {e}")
            return

        if not ranked_jobs:
            return

        # 2. Filter already-notified jobs
        existing_links = {
            match.job.link for match in user.job_matches if match.job and match.notified
        }

        new_jobs = [j for j in ranked_jobs if j["link"] not in existing_links]
        if not new_jobs:
            return

        email_body = "Here are new job matches for you:\n\n"

        for job_data in new_jobs:
            job = db.query(models.Job).filter(models.Job.link == job_data["link"]).first()

            if not job:
                job = models.Job(
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    link=job_data["link"],
                    source=job_data.get("source", "Unknown"),
                )
                db.add(job)
                db.commit()
                db.refresh(job)

            existing_match = (
                db.query(models.UserJobMatch)
                .filter(
                    models.UserJobMatch.user_id == user.id,
                    models.UserJobMatch.job_id == job.id,
                )
                .first()
            )

            if existing_match:
                continue

            match = models.UserJobMatch(
                user_id=user.id,
                job_id=job.id,
                reasoning=job_data.get("reasoning"),
                notified=True,
            )
            db.add(match)

            email_body += (
                f"- {job.title} at {job.company}\n"
                f"  Reason: {match.reasoning}\n"
                f"  Link: {job.link}\n\n"
            )

        db.commit()

        # 3. Send email AFTER DB commit
        if ENABLE_EMAIL_NOTIFICATIONS and user.notify_by_email and user.email:
            send_email(
                user.email,
                "New Job Recommendations Found!",
                email_body,
            )

    except Exception as e:
        logger.error(f"Notification processing failed for user {user_id}: {e}")
    finally:
        db.close()


async def check_for_new_jobs():
    """Background task entry point."""
    logger.info("Running background job check...")

    db = SessionLocal()
    try:
        users = crud.get_users_for_notification(db)
    finally:
        db.close()

    for user in users:
        await process_user_notifications(user.id)
        await asyncio.sleep(2)  # rate limiting


def schedule_job_checks(loop):
    """Start scheduler using an existing asyncio event loop."""
    global _scheduler

    if _scheduler:
        logger.warning("Job scheduler already running. Skipping.")
        return

    _scheduler = AsyncIOScheduler(event_loop=loop)
    _scheduler.add_job(check_for_new_jobs, "interval", hours=6)
    _scheduler.start()

    logger.info("Background job scheduler started.")
