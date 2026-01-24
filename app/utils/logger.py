"""
Central logging configuration module.

This module provides a reusable logger factory with a consistent
format across the application and avoids duplicate handlers.
"""

from __future__ import annotations

import logging

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Create or retrieve a configured logger instance.

    Args:
        name: Name of the logger (usually __name__).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger
