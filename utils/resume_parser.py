import logging

from docx import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> str:
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = []
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text.append(content)
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        return ""


def parse_docx(file_path: str) -> str:
    """Extracts text from a DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error parsing DOCX {file_path}: {e}")
        return ""


def parse_resume(file_path: str) -> str:
    """
    Parses a resume file (PDF or DOCX) and returns its text content.
    """
    extension = file_path.split(".")[-1].lower()

    if extension == "pdf":
        return parse_pdf(file_path)
    elif extension == "docx":
        return parse_docx(file_path)
    else:
        logger.warning(f"Unsupported file format: {extension}")
        return ""
