import logging

# Placeholder for WhatsApp logic (e.g., using Twilio or Meta Graph API)
# This would share the same 'services' and 'database' logic as the Telegram bot.

logger = logging.getLogger(__name__)


def handle_whatsapp_message(sender_id: str, message_body: str):
    """
    Entry point for WhatsApp Webhooks.
    """
    logger.info(f"Received WhatsApp message from {sender_id}: {message_body}")

    # Future Implementation:
    # 1. Check user in DB (using whatsapp_id)
    # 2. Route intent (Job Search vs Resume)
    # 3. Call services.ai_service
    # 4. Send response back via API
    pass
