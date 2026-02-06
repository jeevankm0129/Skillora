import logging
import os
from typing import Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# =========================
# Configuration
# =========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_client: Optional[AsyncOpenAI] = None


def _init_client() -> None:
    """
    Initialize the OpenAI-compatible async client.
    Fail FAST if misconfigured.
    """
    global _client

    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. " "AI features cannot start without a valid LLM provider."
        )

    _client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        timeout=60,
    )

    logger.info(f"LLM initialized | model={OPENAI_MODEL} | base_url={OPENAI_BASE_URL}")


# Initialize immediately (fail-fast on startup)
_init_client()


# =========================
# Public API
# =========================


async def call_llm(prompt: str) -> Optional[str]:
    """
    Central LLM call used by the entire system.

    Rules:
    - NO business logic here
    - NO prompt formatting assumptions
    - Returns raw text or None
    """

    if not _client:
        logger.error("LLM client not initialized.")
        return None

    try:
        response = await _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise, structured AI assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content
        return content.strip() if content else None

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return None
