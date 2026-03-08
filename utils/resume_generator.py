import io
import logging
from typing import Any, Dict, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer 

logger = logging.getLogger(__name__)


def is_valid_entry(text: str) -> bool:
    """Helper to check if the user skipped a section by typing 'none' or 'na'"""
    if not text:
        return False
    clean_text = text.strip().lower()
    return clean_text not in ["none", "na", "n/a", "no", "-"]


def generate_ats_resume_pdf(user_data: Dict[str, Any]) -> Optional[io.BytesIO]:
    """
    Generates a highly structured, simple text ATS-compliant PDF resume.
    """
    logger.info(f"Generating ATS text resume for {user_data.get('name', 'User')}")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    style_name = ParagraphStyle(
        "NameHeader", parent=styles["Heading1"], fontSize=18, spaceAfter=4, alignment=1
    )
    style_contact = ParagraphStyle(
        "ContactInfo", parent=styles["Normal"], fontSize=10, spaceAfter=16, alignment=1
    )
    style_section_header = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=6,
        spaceBefore=12,
        textColor=colors.black,
        borderPadding=0,
        borderwidth=1,
        borderColor=colors.black,
    )
    style_body = ParagraphStyle(
        "BodyText", parent=styles["Normal"], fontSize=10.5, leading=14, spaceAfter=6
    )

    story = []

    # 1. Header
    name = user_data.get("name", "Your Name")
    story.append(Paragraph(f"<b>{name.upper()}</b>", style_name))

    contact = user_data.get("contact", "")
    story.append(Paragraph(contact, style_contact))

    # 2. Education
    if is_valid_entry(user_data.get("education", "")):
        story.append(Paragraph("<b>EDUCATION</b>", style_section_header))
        story.append(Paragraph(user_data["education"], style_body))

    # 3. Skills
    if is_valid_entry(user_data.get("skills", "")):
        story.append(Paragraph("<b>TECHNICAL SKILLS</b>", style_section_header))
        story.append(Paragraph(user_data["skills"], style_body))

    # 4. Projects
    if is_valid_entry(user_data.get("projects", "")):
        story.append(Paragraph("<b>PROJECTS</b>", style_section_header))
        story.append(Paragraph(user_data["projects"], style_body))

    # 5. Internships
    if is_valid_entry(user_data.get("internships", "")):
        story.append(Paragraph("<b>INTERNSHIPS</b>", style_section_header))
        story.append(Paragraph(user_data["internships"], style_body))

    # 6. Experience
    if is_valid_entry(user_data.get("experience", "")):
        story.append(Paragraph("<b>EXPERIENCE</b>", style_section_header))
        story.append(Paragraph(user_data["experience"], style_body))

    # 7. Exams
    if is_valid_entry(user_data.get("exams", "")):
        story.append(Paragraph("<b>COMPETITIVE EXAMS</b>", style_section_header))
        story.append(Paragraph(user_data["exams"], style_body))

    # 8. Extracurricular
    if is_valid_entry(user_data.get("extracurricular", "")):
        story.append(Paragraph("<b>EXTRACURRICULAR ACTIVITIES</b>", style_section_header))
        story.append(Paragraph(user_data["extracurricular"], style_body))

    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"Failed to build PDF: {e}")
        return None
