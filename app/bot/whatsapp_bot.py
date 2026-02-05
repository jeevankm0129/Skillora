"""
WhatsApp bot placeholder.

This module exists ONLY to reserve architecture space for
a future WhatsApp integration.

⚠️ IMPORTANT:
- This bot is NOT initialized
- This bot is NOT imported anywhere
- This bot makes NO real API calls
"""

from __future__ import annotations

from app.utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppBot:
    """
    Future WhatsApp bot interface (placeholder).

    This class documents how WhatsApp integration would
    be structured without implementing functionality.
    """

    def __init__(self) -> None:
        """
        Initialize WhatsApp bot (future).

        TODO (future upgrade):
        - Load WhatsApp credentials
        - Initialize WhatsApp client (Twilio / Meta API)
        """
        logger.info("WhatsAppBot placeholder created")

    def start(self) -> None:
        """
        Start WhatsApp bot service (future).

        TODO (future upgrade):
        - Register webhook endpoints
        - Listen for incoming messages
        """
        logger.info("WhatsAppBot start() called (placeholder)")

    def handle_message(self, user_id: str, message: str) -> None:
        """
        Handle incoming WhatsApp message (future).

        TODO (future upgrade):
        - Route message to resume/job pipeline
        - Send response back to WhatsApp user
        """
        logger.debug(
            "WhatsApp message received (placeholder): user_id=%s, message=%s",
            user_id,
            message,
        )
