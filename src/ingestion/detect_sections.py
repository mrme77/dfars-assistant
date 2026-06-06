"""Detect DFARS section and clause boundaries in extracted page text."""

import re
from collections.abc import Iterable

from src.models import PageText, SectionRecord

SECTION_HEADING_PATTERN = re.compile(
    r"^(?P<section>(?:\d{3}\.\d{4}|\d{3}\.\d{3}-\d{4}|\d{3}\.\d{3}))\s+(?P<title>.+)$"
)


def detect_section_heading(line: str) -> tuple[str, str] | None:
    """Return a DFARS section identifier and title when a line is a heading.

    Args:
        line: Candidate line from extracted PDF text.

    Returns:
        A `(section_id, title)` tuple when matched, otherwise `None`.
    """
    normalized = " ".join(line.strip().split())
    match = SECTION_HEADING_PATTERN.match(normalized)
    if match is None:
        return None
    title = match.group("title").strip()
    if not _looks_like_heading_title(title):
        return None
    return match.group("section"), title


def _looks_like_heading_title(title: str) -> bool:
    """Return whether matched heading text looks like an actual title."""
    if not title:
        return False
    first_character = title[0]
    return first_character.isupper() or first_character.isdigit() or first_character in "\"'("


def build_sections(pages: Iterable[PageText]) -> list[SectionRecord]:
    """Build DFARS section records from extracted pages.

    Args:
        pages: Ordered page text records.

    Returns:
        Section records with page ranges and original text.
    """
    sections: list[SectionRecord] = []
    current_id: str | None = None
    current_title = ""
    current_start = 1
    current_lines: list[str] = []

    for page in pages:
        for line in page.text.splitlines():
            heading = detect_section_heading(line)
            if heading is not None:
                if current_id is not None:
                    sections.append(
                        _make_record(
                            current_id,
                            current_title,
                            current_start,
                            page.page_number,
                            current_lines,
                        )
                    )
                current_id, current_title = heading
                current_start = page.page_number
                current_lines = [line]
                continue

            if current_id is not None:
                current_lines.append(line)

    if current_id is not None:
        final_page = page.page_number if "page" in locals() else current_start
        sections.append(
            _make_record(
                current_id,
                current_title,
                current_start,
                final_page,
                current_lines,
            )
        )

    return sections


def _make_record(
    section_id: str,
    title: str,
    page_start: int,
    page_end: int,
    lines: list[str],
) -> SectionRecord:
    """Create a section record from accumulated text lines."""
    return SectionRecord(
        section_id=section_id,
        title=title,
        part=section_id.split(".", maxsplit=1)[0],
        page_start=page_start,
        page_end=page_end,
        original_text="\n".join(lines).strip(),
    )
