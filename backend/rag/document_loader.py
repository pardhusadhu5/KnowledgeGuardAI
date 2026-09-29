import os
import re
from pathlib import Path
from typing import Tuple
from backend.utils.logger import get_logger

logger = get_logger("document_loader")


def clean_text(text: str) -> str:
    """Cleans extracted document text by stripping excess whitespace and normalizing linebreaks."""
    if not text:
        return ""
    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3 or more newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_file(file_path: Path) -> Tuple[str, str]:
    """
    Extracts and cleans text from PDF or TXT file.
    Returns: (cleaned_text, detected_type)
    """
    suffix = file_path.suffix.lower()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    cleaned = ""
    if suffix == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            pages_text = []
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    pages_text.append(extracted)
            cleaned = clean_text("\n\n".join(pages_text))
            if not cleaned:
                raise ValueError("PDF file contains no extractable text.")
            return cleaned, "pdf"
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {e}")
            raise ValueError(f"Failed to read PDF document: {str(e)}")

    elif suffix in [".txt", ".md", ".json", ".csv"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            cleaned = clean_text(content)
            if not cleaned:
                raise ValueError("Text file is empty.")
            return cleaned, "text"
        except Exception as e:
            logger.error(f"Error extracting text file {file_path}: {e}")
            raise ValueError(f"Failed to read text document: {str(e)}")

    else:
        raise ValueError(f"Unsupported file format: {suffix}. Only PDF and TXT documents are supported.")
