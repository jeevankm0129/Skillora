"""ATS-friendly PDF resume generator.

This module is intentionally additive and does not alter the existing
`utils.resume_generator` behavior. It can be integrated into the current
pipeline by importing and calling `generate_ats_pdf_resume` where appropriate.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Iterable, List, Sequence

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)

DEFAULT_SECTION_ORDER: Sequence[str] = (
    "Summary",
    "Skills",
    "Experience",
    "Education",
    "Projects",
)

SECTION_ALIAS_MAP: Dict[str, str] = {
    "summary": "Summary",
    "professional summary": "Summary",
    "skills": "Skills",
    "technical skills": "Skills",
    "experience": "Experience",
    "work experience": "Experience",
    "education": "Education",
    "projects": "Projects",
}


def _normalize_line(text: str) -> str:
    """Normalize whitespace while preserving readable sentence spacing."""
    return re.sub(r"\s+", " ", text).strip()


def _clean_inline_markup(text: str) -> str:
    """Remove decorative markdown markers to keep ATS text machine-readable."""
    cleaned = text.replace("**", "")
    cleaned = cleaned.replace("__", "")
    cleaned = cleaned.replace("`", "")
    return _normalize_line(cleaned)


def _normalize_heading(line: str) -> str | None:
    """Map free-form heading text to one of the standard ATS section names."""
    candidate = line.strip().strip(":")
    if not candidate:
        return None

    key = candidate.lower()
    return SECTION_ALIAS_MAP.get(key)


def _split_into_sections(
    resume_text: str,
    section_order: Sequence[str] = DEFAULT_SECTION_ORDER,
) -> Dict[str, List[str]]:
    """Split plain-text resume into ATS sections using a single linear pass.

    Complexity is O(n) in number of lines.
    """
    sections: Dict[str, List[str]] = {section: [] for section in section_order}
    active_section = "Summary"

    for raw_line in resume_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        detected_section = _normalize_heading(line)
        if detected_section:
            active_section = detected_section
            continue

        cleaned_line = _clean_inline_markup(line)
        if cleaned_line:
            sections[active_section].append(cleaned_line)

    return sections


def _escape_reportlab_text(text: str) -> str:
    """Escape XML-sensitive characters for ReportLab Paragraph usage."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _build_document_story(
    sections: Dict[str, List[str]],
    section_order: Sequence[str],
) -> List:
    """Build a memory-efficient, single-column Platypus story list."""
    heading_style = ParagraphStyle(
        "AtsHeading",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=6,
        spaceBefore=10,
    )
    body_style = ParagraphStyle(
        "AtsBody",
        fontName="Helvetica",
        fontSize=10.5,
        leading=13,
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    story: List = []
    for section_name in section_order:
        lines = sections.get(section_name, [])
        if not lines:
            continue

        story.append(Paragraph(_escape_reportlab_text(section_name), heading_style))
        for line in lines:
            story.append(Paragraph(_escape_reportlab_text(line), body_style))
        story.append(Spacer(1, 6))

    return story


def generate_ats_pdf_resume(
    resume_text: str,
    output_path: str,
    section_order: Sequence[str] = DEFAULT_SECTION_ORDER,
) -> bool:
    """Generate a clean ATS-friendly resume PDF from plain text.

    Args:
        resume_text: Raw resume text.
        output_path: Target PDF file path.
        section_order: Ordered ATS section names to render.

    Returns:
        True when PDF generation succeeds, False otherwise.
    """
    try:
        sections = _split_into_sections(resume_text, section_order=section_order)
        story = _build_document_story(sections, section_order)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40,
            title="ATS Resume",
            author="Skillora",
        )
        doc.build(story)

        logger.info("ATS-friendly PDF generated successfully: %s", output_path)
        return True
    except Exception as exc:  # preserve fail-safe behavior used in existing generator
        logger.error("Error generating ATS-friendly PDF resume: %s", exc)
        return False


def generate_ats_pdf_resume_from_sections(
    section_content: Dict[str, Iterable[str]],
    output_path: str,
    section_order: Sequence[str] = DEFAULT_SECTION_ORDER,
) -> bool:
    """Generate ATS resume from pre-structured section content.

    This is a reusable integration helper for future services that already
    maintain structured resume content.
    """
    merged_sections: Dict[str, List[str]] = {section: [] for section in section_order}
    for section_name, entries in section_content.items():
        normalized_section = _normalize_heading(section_name) or section_name
        if normalized_section not in merged_sections:
            continue
        merged_sections[normalized_section].extend(
            _clean_inline_markup(str(entry)) for entry in entries if str(entry).strip()
        )

    story = _build_document_story(merged_sections, section_order)

    try:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40,
            title="ATS Resume",
            author="Skillora",
        )
        doc.build(story)
        logger.info("ATS-friendly PDF generated from structured sections: %s", output_path)
        return True
    except Exception as exc:
        logger.error("Error generating ATS resume from sections: %s", exc)
        return False
