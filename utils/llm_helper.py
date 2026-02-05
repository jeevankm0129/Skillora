import logging

import google.generativeai as genai

from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

model = None


def configure_gemini():
    """Initializes the Gemini model safely."""
    global model
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is missing. AI features will be disabled.")
        return

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Using the latest stable Flash model for speed and cost
        model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("Gemini AI successfully configured.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini AI: {e}")


# Initialize on import
configure_gemini()


async def call_gemini(prompt: str) -> str | None:
    """
    Sends a prompt to Gemini and returns the text response.
    Returns None if the call fails.
    """
    if not model:
        logger.error("Attempted to call Gemini, but model is not initialized.")
        return None

    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return None
