"""
Resume builder module.

Builds an ATS-friendly resume from structured user-provided data.
Returns the resume as an in-memory PDF or DOCX file.
"""

from __future__ import annotations

import io
from typing import Dict, Literal, Optional

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.utils.logger import get_logger

logger = get_logger(__name__)

ResumeFormat = Literal["pdf", "docx"]


class ResumeBuilderError(Exception):
    """Raised when resume generation fails."""


class ResumeBuilder:
    """
    Build resume documents from structured user input.
    """

    def build(
        self,
        user_data: Dict[str, object],
        output_format: ResumeFormat = "docx",
        enhanced_text: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """
        Build a resume.

        Args:
            Details(name, email, phone, skills, education, experience)
            output_format: 'pdf' or 'docx'
            enhanced_text: Optional AI-enhanced section text

        Returns:
            Resume file as bytes.
        """
        logger.info("Generating resume (format=%s)", output_format)

        try:
            if output_format == "docx":
                return self._build_docx(user_data, enhanced_text)
            if output_format == "pdf":
                return self._build_pdf(user_data, enhanced_text)

            raise ResumeBuilderError("Unsupported resume format")

        except Exception as exc:
            logger.error("Resume generation failed: %s", exc)
            raise ResumeBuilderError("Resume build failed") from exc

    # ==================================================
    # DOCX
    # ==================================================

    def _build_docx(
        self,
        user_data: Dict[str, object],
        enhanced_text: Optional[Dict[str, str]],
    ) -> bytes:
        document = Document()

        self._add_header_docx(document, user_data)
        self._add_section_docx(
            document,
            "Education",
            self._get_section_text("education", user_data, enhanced_text),
        )
        self._add_section_docx(
            document,
            "Experience",
            self._get_section_text("experience", user_data, enhanced_text),
        )
        self._add_section_docx(
            document,
            "Skills",
            self._format_skills(user_data.get("skills")),
        )

        buffer = io.BytesIO()
        document.save(buffer)
        buffer.seek(0)

        logger.info("DOCX resume generated successfully")
        return buffer.read()

    # ==================================================
    # PDF
    # ==================================================

    def _build_pdf(
        self,
        user_data: Dict[str, object],
        enhanced_text: Optional[Dict[str, str]],
    ) -> bytes:
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        _, height = A4

        y_position = height - 40

        def draw_line(text: str) -> None:
            nonlocal y_position
            if y_position < 40:
                pdf.showPage()
                y_position = height - 40
            pdf.drawString(40, y_position, text)
            y_position -= 16

        draw_line(str(user_data.get("name", "")))
        draw_line(str(user_data.get("email", "")))
        draw_line(str(user_data.get("phone", "")))
        y_position -= 20

        draw_line("Education")
        draw_line(self._get_section_text("education", user_data, enhanced_text))
        y_position -= 10

        draw_line("Experience")
        draw_line(self._get_section_text("experience", user_data, enhanced_text))
        y_position -= 10

        draw_line("Skills")
        draw_line(self._format_skills(user_data.get("skills")))

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        logger.info("PDF resume generated successfully")
        return buffer.read()

    # ==================================================
    # HELPERS
    # ==================================================

    def _add_header_docx(self, document, user_data: Dict[str, object]) -> None:
        document.add_heading(str(user_data.get("name", "")), level=1)
        document.add_paragraph(str(user_data.get("email", "")))
        document.add_paragraph(str(user_data.get("phone", "")))

    def _add_section_docx(self, document, title: str, content: str) -> None:
        document.add_heading(title, level=2)
        document.add_paragraph(content)

    def _get_section_text(
        self,
        key: str,
        user_data: Dict[str, object],
        enhanced_text: Optional[Dict[str, str]],
    ) -> str:
        if enhanced_text and key in enhanced_text:
            return enhanced_text[key]

        value = user_data.get(key)
        return value if isinstance(value, str) else ""

    def _format_skills(self, skills: object) -> str:
        if isinstance(skills, list):
            return ", ".join(str(skill) for skill in skills)
        return ""
