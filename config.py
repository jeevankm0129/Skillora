"""
config.py
---------
Central configuration module.  All values are read from environment
variables (populated by a .env file via python-dotenv).

Required variables:
  TELEGRAM_BOT_TOKEN   — Telegram BotFather token
  DATABASE_URL         — Async-driver DB URL (see below)

Optional variables (have safe defaults):
  ENV                  — 'development' | 'production'  (default: development)
  LOG_LEVEL            — Python log level string        (default: INFO)
  WHATSAPP_VERIFY_TOKEN
  WHATSAPP_API_TOKEN
  ENABLE_EMAIL_NOTIFICATIONS  — 'true' | 'false'       (default: true)
  SMTP_SERVER          — e.g. smtp.gmail.com
  SMTP_PORT            — e.g. 587
  SMTP_EMAIL
  SMTP_PASSWORD

DATABASE_URL must use an async driver:
  SQLite   →  sqlite+aiosqlite:///./skillora.db
  Postgres →  postgresql+asyncpg://user:pass@host/db
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------
ENV       = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./skillora.db")

_VALID_ASYNC_PREFIXES = ("sqlite+aiosqlite", "postgresql+asyncpg")
if not any(DATABASE_URL.startswith(p) for p in _VALID_ASYNC_PREFIXES):
    raise RuntimeError(
        f"DATABASE_URL must use an async driver.\n"
        f"  Got:      {DATABASE_URL!r}\n"
        f"  Expected: 'sqlite+aiosqlite://...'  or  'postgresql+asyncpg://...'"
    )

# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not TELEGRAM_BOT_TOKEN:
    # Log a warning rather than raising at import time.
    # The application will fail with a clear message when it tries to start
    # the Telegram bot, which is the right place for that error.
    logger.warning(
        "TELEGRAM_BOT_TOKEN is not set. "
        "The Telegram bot will not start without it."
    )

# ---------------------------------------------------------------------------
# WhatsApp (placeholder — not yet active)
# ---------------------------------------------------------------------------
WHATSAPP_VERIFY_TOKEN: str = os.getenv(
    "WHATSAPP_VERIFY_TOKEN", "SKILLORA_SECRET_TOKEN_123"
)
WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")

# ---------------------------------------------------------------------------
# Email / SMTP
# ---------------------------------------------------------------------------
ENABLE_EMAIL_NOTIFICATIONS: bool = (
    os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "true").strip().lower() == "true"
)
SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT:   int = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL:  str = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

if ENABLE_EMAIL_NOTIFICATIONS and not all([SMTP_EMAIL, SMTP_PASSWORD]):
    logger.warning(
        "Email notifications are enabled (ENABLE_EMAIL_NOTIFICATIONS=true) "
        "but SMTP_EMAIL or SMTP_PASSWORD is missing. Emails will not be sent."
    )
