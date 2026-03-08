import asyncio
import logging
import smtplib
from email.mime.text import MIMEText

from config import SMTP_EMAIL, SMTP_PASSWORD, SMTP_PORT, SMTP_SERVER

logger = logging.getLogger(__name__)


def _send_email_sync(to_email: str, subject: str, body: str) -> bool:
    """The underlying native synchronous email logic."""
    if not all([SMTP_EMAIL, SMTP_PASSWORD, SMTP_SERVER]):
        logger.warning("SMTP settings missing. Skipping email.")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
            logger.info(f"Email sent successfully to {to_email}")
            return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Async wrapper: Offloads the blocking SMTP handshake to a background thread.
    This ensures the bot UI never freezes while waiting for the email server.
    """
    return await asyncio.to_thread(_send_email_sync, to_email, subject, body)
