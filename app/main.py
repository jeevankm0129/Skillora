"""
Application entry point.
"""

from app.bot.telegram_bot import start_bot
from app.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Start the Skillora application."""
    try:
        logger.info("Starting application")
        start_bot()
    except Exception as exc:
        logger.exception("Application failed to start")
        raise exc


if __name__ == "__main__":
    main()
