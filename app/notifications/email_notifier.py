"""
Email notification service.

This module is responsible for sending email notifications
using SMTP with secure credential handling, retries, and logging.
"""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from app.config import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailNotificationError(Exception):
    """Raised when email delivery fails."""


class EmailNotifier:
    """
    Email notification service using SMTP.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """
        Initialize EmailNotifier with validated configuration.
        """
        settings = settings or Settings()

        # Explicit runtime + type narrowing (Pylance understands this)
        assert settings.EMAIL_HOST is not None
        assert settings.EMAIL_PORT is not None
        assert settings.EMAIL_USER is not None
        assert settings.EMAIL_PASSWORD is not None

        self._email_host: str = settings.EMAIL_HOST
        self._email_port: int = int(settings.EMAIL_PORT)
        self._email_user: str = settings.EMAIL_USER
        self._email_password: str = settings.EMAIL_PASSWORD

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        retries: int = 3,
    ) -> None:
        """
        Send an email with retry support.

        Args:
            to_email: Recipient email address.
            subject: Email subject.
            body: Email body text.
            retries: Number of retry attempts.

        Raises:
            EmailNotificationError: If email cannot be sent.
        """
        logger.info("Sending email to %s", to_email)

        message = EmailMessage()
        message["From"] = self._email_user
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        context = ssl.create_default_context()

        for attempt in range(1, retries + 1):
            try:
                with smtplib.SMTP(self._email_host, self._email_port) as server:
                    server.starttls(context=context)
                    server.login(self._email_user, self._email_password)
                    server.send_message(message)

                logger.info(
                    "Email successfully sent to %s (attempt %d)",
                    to_email,
                    attempt,
                )
                return

            except Exception as exc:
                logger.error(
                    "Email send attempt %d failed: %s",
                    attempt,
                    exc,
                )

                if attempt == retries:
                    raise EmailNotificationError("Failed to send email after retries") from exc
