"""Tests for vector search helper functions."""

from src.models import SectionRecord
from src.retrieval.vector_search import _embedding_text, _middle_truncate, _normalize_vector


def test_embedding_text_contains_metadata() -> None:
    """It embeds structured metadata plus source text."""
    section = SectionRecord(
        section_id="252.204-7012",
        title="Safeguarding Covered Defense Information.",
        page_start=1,
        page_end=2,
        original_text="The contractor shall provide adequate security.",
        key_topics=["covered defense information"],
        required_actions=["Include the clause when prescribed."],
    )

    text = _embedding_text(section)

    assert "DFARS 252.204-7012" in text
    assert "covered defense information" in text
    assert "Include the clause when prescribed." in text


def test_middle_truncate_preserves_head_and_tail() -> None:
    """It truncates long embedding text without dropping both ends."""
    text = "a" * 100 + "middle" + "z" * 100

    truncated = _middle_truncate(text, 80)

    assert truncated.startswith("a")
    assert truncated.endswith("z")
    assert "truncated for embedding" in truncated


def test_normalize_vector_returns_unit_length() -> None:
    """It normalizes vectors before storing them in Chroma."""
    vector = _normalize_vector([3.0, 4.0])

    assert vector == [0.6, 0.8]
