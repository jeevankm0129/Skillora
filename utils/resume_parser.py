import io
import logging
from typing import List

import pdfplumber
from docx import Document

logger = logging.getLogger(__name__)


def parse_resume(file_bytes: io.BytesIO, extension: str) -> str:
    """
    Extracts text from an in-memory document stream.
    Supports: PDF (text-based) and DOCX.
    """
    try:
        if extension == "pdf":
            text_parts: List[str] = []
            # pdfplumber natively accepts BytesIO objects
            with pdfplumber.open(file_bytes) as pdf:
                for page in pdf.pages:
                    content = page.extract_text()
                    if content:
                        text_parts.append(content)
            return "\n".join(text_parts).strip()

        elif extension == "docx":
            # python-docx natively accepts BytesIO objects
            doc = Document(file_bytes)
            return "\n".join(para.text.strip() for para in doc.paragraphs if para.text.strip())

        else:
            logger.warning(f"Unsupported file format: {extension}")
            return ""

    except Exception as e:
        logger.error(f"Error parsing document: {e}")
        return ""
