import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from config import ENABLE_EMAIL_NOTIFICATIONS
from database import models
from database.db import AsyncSessionLocal
from services.ai_service import get_job_recommendations
from utils.email_sender import send_email

logger = logging.getLogger(__name__)

_scheduler = None  # Singleton to prevent duplicate schedulers


async def process_user_notifications(user_id: int):
    """
    Hunts for new jobs for a single user in the background.
    """
    async with AsyncSessionLocal() as db:
        # Load user, their resume, and their past job matches
        stmt = (
            select(models.User)
            .options(
                selectinload(models.User.resume),
                selectinload(models.User.job_matches).selectinload(models.UserJobMatch.job),
            )
            .where(models.User.id == user_id)
        )

        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user or not user.resume or not user.resume.text_content:
            return

        # 1. Ask AI for fresh job recommendations
        try:
            ranked_jobs = await get_job_recommendations(
                skills=[], resume_text=user.resume.text_content
            )
        except Exception as e:
            logger.error(f"Background AI hunt failed for user {user.id}: {e}")
            return

        if not ranked_jobs:
            return

        # 2. Filter out jobs we have already sent them
        existing_links = {match.job.link for match in user.job_matches if match.job}

        new_jobs = [j for j in ranked_jobs if j["link"] not in existing_links]
        if not new_jobs:
            return

        # 3. Save new jobs to DB and prepare notification
        email_body = "Good news! Skillora found new job matches for you:\n\n"

        for job_data in new_jobs:
            # Check if job exists in the global DB
            job_stmt = select(models.Job).where(models.Job.link == job_data["link"])
            job_res = await db.execute(job_stmt)
            job = job_res.scalars().first()

            if not job:
                job = models.Job(
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    link=job_data["link"],
                    source=job_data.get("source", "API"),
                )
                db.add(job)
                await db.flush()  # Get the new Job ID safely

            # Create the link between User and Job
            match = models.UserJobMatch(
                user_id=user.id,
                job_id=job.id,
                relevance_score=job_data.get("score", 0),
                notified=True,
            )
            db.add(match)

            email_body += (
                f"- {job.title} at {job.company}\n"
                f"  Why: {job_data.get('reasoning', 'Great fit!')}\n"
                f"  Apply: {job.link}\n\n"
            )

        await db.commit()  # Commit DB first so we don't spam if email fails

        # 4. Send Notifications
        if ENABLE_EMAIL_NOTIFICATIONS and user.email:
            await send_email(user.email, "Skillora: New Job Alerts!", email_body)

        # TODO: Here you will trigger your WhatsApp/Telegram message sender
        # e.g., await send_whatsapp_message(user.whatsapp_id, "New jobs found! Check your email.")


async def check_for_new_jobs():
    """The main loop that runs every 2 hours."""
    logger.info("Running automated job hunt...")

    async with AsyncSessionLocal() as db:
        stmt = select(models.User.id).where(models.User.background_tracking_enabled == True)
        result = await db.execute(stmt)
        user_ids = result.scalars().all()

    for uid in user_ids:
        await process_user_notifications(uid)
        await asyncio.sleep(2)  # Rate limit API calls so we don't get banned


def schedule_job_checks(loop):
    """Starts the scheduler. We will call this from FastAPI startup."""
    global _scheduler
    if _scheduler:
        return

    _scheduler = AsyncIOScheduler(event_loop=loop)
    # Runs every 2 hours
    _scheduler.add_job(check_for_new_jobs, "interval", hours=2)
    _scheduler.start()
    logger.info("Background job hunter started (2-Hour Interval).")
