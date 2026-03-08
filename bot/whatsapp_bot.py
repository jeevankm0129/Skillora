import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

# This router is imported by main.py to keep the architecture intact
whatsapp_router = APIRouter()


@whatsapp_router.get("/webhook")
async def verify_whatsapp_webhook(request: Request):
    """
    Placeholder: Meta/WhatsApp requires a GET endpoint for webhook verification.
    """
    logger.info("WhatsApp GET webhook hit (Placeholder).")
    return {"status": "WhatsApp integration is currently paused."}


@whatsapp_router.post("/webhook")
async def handle_whatsapp_message(request: Request):
    """
    Placeholder: Where incoming WhatsApp messages will eventually arrive.
    """
    logger.info("WhatsApp POST webhook hit (Placeholder).")
    # Acknowledge the message so Meta doesn't think our server is dead
    return {"status": "success"}
