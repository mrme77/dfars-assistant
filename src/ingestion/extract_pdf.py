"""Extract text from the DFARS PDF while preserving page numbers."""

from pathlib import Path

import fitz

from src.models import PageText


def extract_pages(pdf_path: Path) -> list[PageText]:
    """Extract text from every page of a PDF.

    Args:
        pdf_path: Path to the source PDF.

    Returns:
        Ordered page text records.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        ValueError: If the path does not point to a PDF file.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file: {pdf_path}")

    pages: list[PageText] = []
    with fitz.open(pdf_path) as document:
        for index, page in enumerate(document, start=1):
            pages.append(PageText(page_number=index, text=page.get_text("text")))
    return pages

