"""Build JSONL section chunks from the DFARS PDF."""

import json
from pathlib import Path

from src.ingestion.detect_sections import build_sections
from src.ingestion.extract_pdf import extract_pages


def build_section_index(pdf_path: Path, output_path: Path) -> int:
    """Extract section records from a PDF and write them as JSONL.

    Args:
        pdf_path: Source DFARS PDF path.
        output_path: Destination JSONL path.

    Returns:
        Number of section records written.
    """
    pages = extract_pages(pdf_path)
    sections = build_sections(pages)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for section in sections:
            output_file.write(json.dumps(section.model_dump(), ensure_ascii=False) + "\n")

    return len(sections)


if __name__ == "__main__":
    count = build_section_index(
        Path("Data/DFARS.pdf"),
        Path("indexes/dfars_sections.jsonl"),
    )
    print(f"Wrote {count} DFARS sections.")

