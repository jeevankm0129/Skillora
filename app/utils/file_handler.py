"""
File handling utilities.

This module provides secure helpers for validating and saving
uploaded resume files while preventing common file-based attacks.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import BinaryIO, Set


class FileValidationError(Exception):
    """Raised when file validation fails."""


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------


ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx"}
MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB


# ---------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------


def validate_file_extension(filename: str) -> None:
    """
    Validate allowed file extensions.
    """
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type: {suffix}. " f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def validate_file_size(file_obj: BinaryIO) -> None:
    """
    Validate uploaded file size.
    """
    current_position = file_obj.tell()
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(current_position)

    if size > MAX_FILE_SIZE_BYTES:
        raise FileValidationError("File size exceeds allowed limit (5 MB)")


# ---------------------------------------------------------------------
# Secure file saving
# ---------------------------------------------------------------------


def save_file_securely(
    file_obj: BinaryIO,
    filename: str,
    destination_dir: Path,
) -> Path:
    """
    Save a file securely to the destination directory.

    - Prevents path traversal
    - Validates file type and size
    - Ensures destination directory exists

    Args:
        file_obj: File-like object opened in binary mode.
        filename: Original filename.
        destination_dir: Directory where file should be stored.

    Returns:
        Path to the saved file.
    """
    validate_file_extension(filename)
    validate_file_size(file_obj)

    destination_dir = destination_dir.resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name
    target_path = (destination_dir / safe_name).resolve()

    # Prevent path traversal
    if not str(target_path).startswith(str(destination_dir)):
        raise FileValidationError("Invalid file path detected")

    with target_path.open("wb") as target_file:
        shutil.copyfileobj(file_obj, target_file)

    return target_path
