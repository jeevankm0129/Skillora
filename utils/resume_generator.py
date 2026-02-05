import logging
import re

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)


def clean_markdown_for_pdf(text: str) -> str:
    """Converts Markdown bold (**text**) to ReportLab XML (<b>text</b>)."""
    # Replace **text** with <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Replace *text* with <i>text</i>
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    # Replace newlines with <br/> for ReportLab
    text = text.replace("\n", "<br/>")
    return text


def generate_pdf_resume(text_content: str, output_path: str) -> bool:
    """Generates a professionally formatted PDF resume."""
    try:
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()

        # Custom style for resume text
        resume_style = ParagraphStyle(
            "ResumeBody",
            parent=styles["Normal"],
            fontSize=11,
            leading=15,
            alignment=TA_LEFT,
            spaceAfter=10,
        )

        story = []

        # Split by double newlines to separate paragraphs
        paragraphs = text_content.split("\n\n")

        for para in paragraphs:
            if not para.strip():
                continue

            formatted_text = clean_markdown_for_pdf(para)
            story.append(Paragraph(formatted_text, resume_style))
            story.append(Spacer(1, 6))

        doc.build(story)
        logger.info(f"PDF generated successfully: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error generating PDF resume: {e}")
        return False
