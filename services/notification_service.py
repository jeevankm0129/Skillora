import asyncio
import logging

from sqlalchemy.future import select

from config import ENABLE_EMAIL_NOTIFICATIONS
from database import crud, models
from database.db import AsyncSessionLocal, get_db_context
from services.ai_service import get_job_recommendations
from utils.email_sender import send_email

logger = logging.getLogger(__name__)

_scheduler = None  # Singleton guard


# ---------------------------------------------------------------------------
# Per-user notification processor
# ---------------------------------------------------------------------------

async def process_user_notifications(user: models.User) -> None:
    """
    Finds new job matches for a single user and notifies them.
    Isolated per-user so one failure never blocks the others.
    """
    if not user.resume or not user.resume.text_content:
        logger.info(f"User {user.id} has no resume — skipping.")
        return

    # 1. Fresh job recommendations
    try:
        ranked_jobs = await get_job_recommendations(
            skills=[], resume_text=user.resume.text_content
        )
    except Exception as e:
        logger.error(f"Job fetch failed for user {user.id}: {e}", exc_info=True)
        return

    if not ranked_jobs:
        logger.info(f"No new jobs found for user {user.id}.")
        return

    # 2. Filter jobs the user has already seen
    existing_links = {
        match.job.link for match in user.job_matches if match.job
    }
    new_jobs = [j for j in ranked_jobs if j.get("link") and j["link"] not in existing_links]

    if not new_jobs:
        logger.info(f"No *new* jobs for user {user.id} — all already notified.")
        return

    # 3. Persist new jobs + matches, then notify
    email_lines: list[str] = []

    async with get_db_context() as db:
        for job_data in new_jobs:
            try:
                link = job_data["link"]

                # Upsert Job record
                job_stmt = select(models.Job).where(models.Job.link == link)
                job_res = await db.execute(job_stmt)
                job = job_res.scalars().first()

                if not job:
                    job = models.Job(
                        title=job_data.get("title", "Unknown"),
                        company=job_data.get("company", "Unknown"),
                        location=job_data.get("location", "Remote"),
                        link=link,
                        source=job_data.get("source", "API"),
                    )
                    db.add(job)
                    await db.flush()   # Populate job.id before creating match
                    await db.refresh(job)

                # Create UserJobMatch
                match = models.UserJobMatch(
                    user_id=user.id,
                    job_id=job.id,
                    relevance_score=job_data.get("score", 0),
                    notified=True,
                )
                db.add(match)

                email_lines.append(
                    f"• {job.title} at {job.company}\n"
                    f"  Why: {job_data.get('reasoning', 'Great fit!')}\n"
                    f"  Apply: {job.link}"
                )

            except Exception as e:
                # Skip this job but continue processing others
                logger.error(
                    f"Failed to save job '{job_data.get('title')}' for user {user.id}: {e}",
                    exc_info=True,
                )

        # Commit happens here via get_db_context __aexit__

    # 4. Send email notification (after commit so data is safe first)
    if email_lines and ENABLE_EMAIL_NOTIFICATIONS and user.email:
        body = (
            "Good news! Skillora found new job matches for you:\n\n"
            + "\n\n".join(email_lines)
        )
        await send_email(user.email, "Skillora: New Job Alerts!", body)
        logger.info(f"Email sent to {user.email} with {len(email_lines)} new job(s).")


# ---------------------------------------------------------------------------
# Main scheduler job
# ---------------------------------------------------------------------------

async def check_for_new_jobs() -> None:
    """
    Runs every 2 hours. Fetches all active users and processes each one.
    Per-user failures are isolated — one bad user never stops the rest.
    """
    logger.info("Background job hunt started.")

    async with get_db_context() as db:
        users = await crud.get_users_for_background_check(db)

    logger.info(f"Checking {len(users)} active user(s).")

    for user in users:
        try:
            await process_user_notifications(user)
        except Exception as e:
            logger.error(f"Unhandled error processing user {user.id}: {e}", exc_info=True)

        # Polite rate-limiting between users
        await asyncio.sleep(2)

    logger.info("Background job hunt complete.")


# ---------------------------------------------------------------------------
# Scheduler bootstrap
# ---------------------------------------------------------------------------

def schedule_job_checks(loop: asyncio.AbstractEventLoop) -> None:
    """
    Starts the APScheduler async scheduler.
    Called once from FastAPI lifespan — guarded against duplicate starts.
    """
    global _scheduler
    if _scheduler is not None:
        logger.warning("Scheduler already running — skipping duplicate start.")
        return

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        # FIX: event_loop parameter removed — deprecated in APScheduler 4.x
        _scheduler = AsyncIOScheduler()
        _scheduler.add_job(check_for_new_jobs, "interval", hours=2, max_instances=1)
        _scheduler.start()
        logger.info("Background job scheduler started (2-hour interval).")

    except ImportError:
        logger.error(
            "APScheduler not installed. Background job checks are disabled. "
            "Install with: pip install apscheduler"
        )
