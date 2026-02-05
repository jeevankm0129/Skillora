import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import crud, models
from database.database import SessionLocal
from services.ai_service import rank_jobs
from services.job_fetcher import fetch_jobs
from utils.email_sender import send_email

logger = logging.getLogger(__name__)


async def process_user_notifications(user_id: int):
    """Checks for new jobs for a single user and notifies them."""
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user or not user.resume:
            return

        # 1. Get Keywords (stored in Resume JSON or fallback to Skills)
        # Ideally, we saved 'search_keywords' in resume.parsed_json
        # For now, we'll derive from skills if JSON is missing
        keywords = []
        if user.skills:
            keywords = [s.name for s in user.skills][:3]  # Take top 3 skills

        if not keywords:
            return

        # 2. Fetch Jobs
        raw_jobs = await fetch_jobs(keywords)
        if not raw_jobs:
            return

        # 3. Filter out jobs already matched/notified
        existing_links = {match.job.link for match in user.job_matches if match.job}

        new_jobs = [j for j in raw_jobs if j["link"] not in existing_links]

        if not new_jobs:
            return

        # 4. Rank with AI
        ranked_jobs = await rank_jobs(new_jobs, user.resume.text_content)

        if not ranked_jobs:
            return

        # 5. Save Matches to DB & Notify
        email_body = "Here are new job matches for you:\n\n"

        for job_data in ranked_jobs:
            # Create Job record if not exists
            job = db.query(models.Job).filter(models.Job.link == job_data["link"]).first()
            if not job:
                job = models.Job(
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    link=job_data["link"],
                    source=job_data["source"],
                )
                db.add(job)
                db.commit()
                db.refresh(job)

            # Create Match Record
            match = models.UserJobMatch(
                user_id=user.id, job_id=job.id, reasoning=job_data.get("reasoning"), notified=True
            )
            db.add(match)

            email_body += f"- {job.title} at {job.company}\n  Reason: {match.reasoning}\n  Link: {job.link}\n\n"

        db.commit()

        # 6. Send Email
        if user.notify_by_email and user.email:
            send_email(user.email, "New Job Recommendations Found!", email_body)

    except Exception as e:
        logger.error(f"Error processing notifications for user {user_id}: {e}")
    finally:
        db.close()


async def check_for_new_jobs():
    """Background task entry point."""
    logger.info("Running background job check...")
    db = SessionLocal()
    try:
        users = crud.get_users_for_notification(db)
        for user in users:
            await process_user_notifications(user.id)
            await asyncio.sleep(2)  # Prevent rate limiting
    finally:
        db.close()


def schedule_job_checks():
    """Starts the scheduler."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_for_new_jobs, "interval", hours=6)
    scheduler.start()
    logger.info("Background scheduler started.")
