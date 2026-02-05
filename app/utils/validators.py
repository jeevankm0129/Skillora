"""
Input validation utilities.

This module provides reusable helpers for validating and
sanitizing user-provided input.
"""

from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------


_EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_valid_email(email: Optional[str]) -> bool:
    """
    Validate an email address.

    Args:
        email: Email string to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not email:
        return False

    return bool(_EMAIL_REGEX.fullmatch(email.strip()))


# ---------------------------------------------------------------------
# Phone number validation
# ---------------------------------------------------------------------


_PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")


def is_valid_phone(phone: Optional[str]) -> bool:
    """
    Validate an international phone number.

    Supports E.164-like formats.

    Args:
        phone: Phone number string.

    Returns:
        True if valid, False otherwise.
    """
    if not phone:
        return False

    return bool(_PHONE_REGEX.fullmatch(phone.strip()))


# ---------------------------------------------------------------------
# General sanitization
# ---------------------------------------------------------------------


def sanitize_text(text: Optional[str], max_length: int = 5000) -> str:
    """
    Sanitize free-text input.

    - Strips whitespace
    - Removes control characters
    - Truncates to a safe length

    Args:
        text: Input text.
        max_length: Maximum allowed length.

    Returns:
        Sanitized string.
    """
    if not text:
        return ""

    cleaned = text.strip()
    cleaned = re.sub(r"[\x00-\x1F\x7F]", "", cleaned)

    return cleaned[:max_length]


def sanitize_string(value: Optional[str], max_length: int = 255) -> Optional[str]:
    """
    Sanitize short string fields (names, titles, etc.).

    Args:
        value: Input string.
        max_length: Maximum allowed length.

    Returns:
        Sanitized string or None.
    """
    if value is None:
        return None

    value = value.strip()
    value = re.sub(r"[\x00-\x1F\x7F]", "", value)

    return value[:max_length]
