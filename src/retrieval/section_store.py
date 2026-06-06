"""Load and query persisted DFARS section records."""

import json
from pathlib import Path

from pydantic import ValidationError

from src.models import SectionRecord


def load_sections(index_path: Path) -> list[SectionRecord]:
    """Load DFARS section records from a JSONL index.

    Args:
        index_path: Path to the section JSONL file.

    Returns:
        Section records in index order.

    Raises:
        FileNotFoundError: If the index path does not exist.
        RuntimeError: If a JSONL row cannot be parsed.
    """
    if not index_path.exists():
        raise FileNotFoundError(f"Section index not found: {index_path}")

    sections: list[SectionRecord] = []
    with index_path.open(encoding="utf-8") as index_file:
        for line_number, line in enumerate(index_file, start=1):
            if not line.strip():
                continue
            try:
                sections.append(SectionRecord.model_validate(json.loads(line)))
            except (json.JSONDecodeError, ValidationError) as exc:
                raise RuntimeError(
                    f"Invalid section record at {index_path}:{line_number}"
                ) from exc
    return sections


class SectionStore:
    """In-memory lookup store for DFARS sections."""

    def __init__(self, sections: list[SectionRecord]) -> None:
        """Initialize a section lookup store.

        Args:
            sections: Section records to index by identifier.
        """
        self.sections = sections
        self._by_id: dict[str, list[SectionRecord]] = {}
        for section in sections:
            self._by_id.setdefault(section.section_id.lower(), []).append(section)

    def exact_lookup(self, section_id: str) -> list[SectionRecord]:
        """Return records for an exact DFARS section identifier.

        Args:
            section_id: DFARS section or clause identifier.

        Returns:
            Matching section records.
        """
        return self._by_id.get(section_id.lower(), [])

