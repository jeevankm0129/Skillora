"""
Central configuration module for the application.

This module is responsible only for loading and exposing
environment-based configuration values in a safe, typed manner.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv


class Settings:
    """
    Application settings loaded from environment variables.

    This class contains no business logic and performs no actions
    other than reading configuration values.
    """

    def __init__(self) -> None:
        # Load environment variables from .env file (if present)
        load_dotenv()

        self.TELE_BOT_TOKEN: Optional[str] = os.getenv("TELE_BOT_TOKEN")
        self.DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

        self.EMAIL_HOST: Optional[str] = os.getenv("EMAIL_HOST")

        email_port = os.getenv("EMAIL_PORT")
        self.EMAIL_PORT: Optional[int] = (
            int(email_port) if email_port is not None else None
        )

        self.EMAIL_USER: Optional[str] = os.getenv("EMAIL_USER")
        self.EMAIL_PASSWORD: Optional[str] = os.getenv("EMAIL_PASSWORD")
