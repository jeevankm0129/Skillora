import logging
import smtplib
from email.mime.text import MIMEText

from config import SMTP_EMAIL, SMTP_PASSWORD, SMTP_PORT, SMTP_SERVER

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an email using the configured SMTP settings.
    Returns True if successful.
    """
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
