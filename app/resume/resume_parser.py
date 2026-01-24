"""
Resume parsing module.

This module is responsible for extracting and normalizing text
from uploaded resume files (PDF or DOCX) and returning a
basic structured representation.

No skill extraction or job logic is implemented here.
"""

from __future__ import annotations

import os
import re
from typing import Dict

from docx import Document
from PyPDF2 import PdfReader

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ResumeParserError(Exception):
    """Custom exception for resume parsing errors."""


class ResumeParser:
    """
    Parse resume files and extract structured information.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

    def parse(self, file_path: str) -> Dict[str, object]:
        """
        Parse a resume file and extract structured data.

        Args:
            file_path: Path to the resume file.

        Returns:
            A dictionary containing extracted resume information.
        """
        logger.info("Starting resume parsing: %s", file_path)

        if not os.path.exists(file_path):
            raise ResumeParserError("Resume file does not exist")

        extension = os.path.splitext(file_path)[1].lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ResumeParserError(f"Unsupported file type: {extension}")

        try:
            if extension == ".pdf":
                raw_text = self._extract_pdf_text(file_path)
            else:
                raw_text = self._extract_docx_text(file_path)

            cleaned_text = self._clean_text(raw_text)

            return {
                "text": cleaned_text,
                "education": self._extract_education(cleaned_text),
                "experience": self._extract_experience(cleaned_text),
            }

        except Exception as exc:
            logger.exception("Failed to parse resume")
            raise ResumeParserError("Resume parsing failed") from exc

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        reader = PdfReader(file_path)
        parts = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                parts.append(page_text)

        return "\n".join(parts)

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from a DOCX file."""
        document = Document(file_path)
        return "\n".join(p.text for p in document.paragraphs if p.text)

    def _clean_text(self, text: str) -> str:
        """Normalize extracted text."""
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\x00-\x7F]+", " ", text)
        return text.strip()

    def _extract_education(self, text: str) -> str:
        """Extract education section (heuristic)."""
        match = re.search(
            r"(education|qualification)(.*?)(experience|skills|projects|$)",
            text,
        )
        return match.group(2).strip() if match else ""

    def _extract_experience(self, text: str) -> str:
        """Extract experience section (heuristic)."""
        match = re.search(
            r"(experience|work experience)(.*?)(education|skills|projects|$)",
            text,
        )
        return match.group(2).strip() if match else ""
