import logging
from typing import List

import pdfplumber
from docx import Document

logger = logging.getLogger(__name__)


# ---------------------------
# PDF PARSER (Text-based only)
# ---------------------------
def parse_pdf(file_path: str) -> str:
    """
    Extracts text from a text-based PDF using pdfplumber.
    Works only if the PDF contains selectable text.
    """
    try:
        text_parts: List[str] = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                content = page.extract_text()
                if content:
                    text_parts.append(content)

        return "\n".join(text_parts).strip()

    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        return ""


# ---------------------------
# DOCX PARSER
# ---------------------------
def parse_docx(file_path: str) -> str:
    """
    Extracts text from a DOCX file.
    """
    try:
        doc = Document(file_path)
        return "\n".join(para.text.strip() for para in doc.paragraphs if para.text.strip())
    except Exception as e:
        logger.error(f"Error parsing DOCX {file_path}: {e}")
        return ""


# ---------------------------
# MAIN RESUME PARSER
# ---------------------------
def parse_resume(file_path: str) -> str:
    """
    Detects file type and extracts resume text.
    Supports: PDF (text-based), DOCX
    """
    extension = file_path.split(".")[-1].lower()

    if extension == "pdf":
        return parse_pdf(file_path)
    elif extension == "docx":
        return parse_docx(file_path)
    else:
        logger.warning(f"Unsupported file format: {extension}")
        return ""
