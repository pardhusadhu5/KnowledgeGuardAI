import os
import re
from pathlib import Path
from typing import Tuple, List, Dict, Any, Generator
from backend.utils.logger import get_logger

logger = get_logger("document_loader")

# Configuration for reliable page batching and resource safety on Render Free tier
DEFAULT_PAGE_BATCH_SIZE = 10
MAX_TOTAL_PAGES = 150


def clean_text(text: str) -> str:
    """Cleans extracted document text by stripping excess whitespace and normalizing linebreaks."""
    if not text:
        return ""
    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple horizontal spaces/tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3 or more newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def inspect_document(file_path: Path) -> Tuple[str, int]:
    """
    Quickly inspects document type and total page count without loading all text into memory.
    Returns: (doc_type, total_pages)
    """
    suffix = file_path.suffix.lower()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if suffix == ".pdf":
        import pypdf
        reader = pypdf.PdfReader(str(file_path))
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
        return "pdf", total_pages
    elif suffix in [".txt", ".md", ".json", ".csv"]:
        return "text", 1
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Only PDF and TXT documents are supported.")


def iter_pdf_page_batches(
    file_path: Path,
    batch_size: int = DEFAULT_PAGE_BATCH_SIZE,
    max_total_pages: int = MAX_TOTAL_PAGES
) -> Generator[Dict[str, Any], None, None]:
    """
    Generator yielding batches of pages with 1-based page numbers.
    Does NOT load the entire document text into memory simultaneously,
    preventing memory spikes on memory-constrained environments like Render Free tier.

    Yields dict:
        {
            "batch_index": int,        # 1-indexed (e.g. 1 of 5)
            "total_batches": int,
            "start_page": int,         # 1-indexed (e.g. 1)
            "end_page": int,           # 1-indexed (e.g. 10)
            "total_pages": int,        # total document pages
            "pages": List[Dict[str, Any]] # [{"page_number": p, "text": clean_text}, ...]
        }
    """
    suffix = file_path.suffix.lower()
    if suffix != ".pdf":
        raise ValueError(f"iter_pdf_page_batches expects a PDF file, got: {suffix}")

    import pypdf
    reader = pypdf.PdfReader(str(file_path))

    # Verify password encryption
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

    if total_pages > max_total_pages:
        raise ValueError(
            f"PDF exceeds the maximum allowable limit of {max_total_pages} pages (contains {total_pages} pages). "
            f"For stability on Render Free tier, please upload documents under {max_total_pages} pages."
        )

    # Compute batches
    total_batches = (total_pages + batch_size - 1) // batch_size
    total_extracted_chars = 0

    logger.info(f"Processing PDF '{file_path.name}': {total_pages} pages detected across {total_batches} batch(es) (batch_size={batch_size})")

    for batch_idx in range(1, total_batches + 1):
        start_page = (batch_idx - 1) * batch_size + 1
        end_page = min(batch_idx * batch_size, total_pages)

        batch_pages = []
        for p in range(start_page, end_page + 1):
            try:
                page_obj = reader.pages[p - 1]
                extracted = page_obj.extract_text() or ""
                cleaned = clean_text(extracted)
                total_extracted_chars += len(cleaned)
                batch_pages.append({
                    "page_number": p,
                    "text": cleaned
                })
            except Exception as page_err:
                logger.warning(f"Could not extract text from page {p} of '{file_path.name}': {page_err}")
                batch_pages.append({
                    "page_number": p,
                    "text": ""
                })

        yield {
            "batch_index": batch_idx,
            "total_batches": total_batches,
            "start_page": start_page,
            "end_page": end_page,
            "total_pages": total_pages,
            "pages": batch_pages
        }

    # Verify document has selectable text across all extracted pages
    if total_extracted_chars < 10:
        raise ValueError(
            "This PDF appears to be scanned/image-based and requires OCR. "
            "KnowledgeGuard AI requires text-searchable documents."
        )


def extract_text_from_file(file_path: Path) -> Tuple[str, str]:
    """
    Legacy helper extracting and cleaning text from PDF or TXT file.
    Processes all pages up to MAX_TOTAL_PAGES without hard 30-page truncation.
    Returns: (cleaned_text, detected_type)
    """
    suffix = file_path.suffix.lower()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if suffix == ".pdf":
        all_pages_text = []
        for batch in iter_pdf_page_batches(file_path, batch_size=DEFAULT_PAGE_BATCH_SIZE, max_total_pages=MAX_TOTAL_PAGES):
            for p in batch["pages"]:
                if p["text"]:
                    all_pages_text.append(p["text"])
        combined = "\n\n".join(all_pages_text)
        return combined, "pdf"

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
