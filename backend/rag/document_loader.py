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
            
            # Check for encryption
            if reader.is_encrypted:
                try:
                    decrypted = reader.decrypt("")
                    if not decrypted:
                        raise ValueError("The uploaded PDF is password-protected. Please upload an unencrypted document.")
                except Exception:
                    raise ValueError("The uploaded PDF is password-protected. Please upload an unencrypted document.")

            total_pages = len(reader.pages)
            if total_pages == 0:
                raise ValueError("The uploaded PDF has no pages.")

            # Controlled handling for large PDFs on free-tier environments:
            # Process up to 30 pages to prevent memory spikes or gateway timeouts
            max_pages = 30
            pages_to_process = reader.pages[:max_pages] if total_pages > max_pages else reader.pages
            if total_pages > max_pages:
                logger.warning(f"PDF '{file_path.name}' contains {total_pages} pages. Processing the first {max_pages} pages to prevent timeout.")

            pages_text = []
            for i, page in enumerate(pages_to_process):
                try:
                    extracted = page.extract_text()
                    if extracted and extracted.strip():
                        pages_text.append(extracted)
                except Exception as page_err:
                    logger.warning(f"Could not extract text from page {i+1} of '{file_path.name}': {page_err}")

            raw_combined = "\n\n".join(pages_text)
            cleaned = clean_text(raw_combined)

            if not cleaned or len(cleaned.strip()) < 10:
                raise ValueError(
                    "This PDF appears to be a scanned image or contains no selectable text layer. "
                    "KnowledgeGuard AI requires text-searchable documents."
                )

            logger.info(f"[PDF Parser] Extracted {len(cleaned)} characters from {len(pages_to_process)}/{total_pages} page(s) of '{file_path.name}'")
            return cleaned, "pdf"

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error parsing PDF document {file_path.name}: {e}")
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
