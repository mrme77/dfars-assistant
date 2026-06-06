"""Tests for loading and querying persisted section records."""

import json
from pathlib import Path

from src.retrieval.section_store import SectionStore, load_sections


def test_load_sections_reads_jsonl(tmp_path: Path) -> None:
    """It loads section records from JSONL."""
    index_path = tmp_path / "sections.jsonl"
    index_path.write_text(
        json.dumps(
            {
                "section_id": "204.7302",
                "title": "Policy.",
                "page_start": 1,
                "page_end": 2,
                "original_text": "204.7302 Policy.",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    sections = load_sections(index_path)

    assert sections[0].section_id == "204.7302"


def test_section_store_exact_lookup_is_case_insensitive(tmp_path: Path) -> None:
    """It returns exact section matches regardless of identifier casing."""
    sections = load_sections(_write_test_index(tmp_path))
    store = SectionStore(sections)

    matches = store.exact_lookup("252.204-7012")

    assert len(matches) == 1
    assert matches[0].title == "Safeguarding Covered Defense Information."


def _write_test_index(tmp_path: Path) -> Path:
    """Write a small section index for tests."""
    index_path = tmp_path / "sections.jsonl"
    index_path.write_text(
        json.dumps(
            {
                "section_id": "252.204-7012",
                "title": "Safeguarding Covered Defense Information.",
                "page_start": 10,
                "page_end": 12,
                "original_text": "252.204-7012 Safeguarding Covered Defense Information.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return index_path

