"""Tests for deterministic DFARS section enrichment."""

from src.models import SectionRecord
from src.preprocessing.enrich_sections import enrich_section


def test_enrich_section_extracts_contracting_metadata() -> None:
    """It adds workflow metadata for contracting officer questions."""
    section = SectionRecord(
        section_id="204.7304",
        title="Solicitation provision and contract clauses.",
        part="204",
        page_start=1,
        page_end=2,
        original_text=(
            "204.7304 Solicitation provision and contract clauses. "
            "The contracting officer shall include the clause at 252.204-7012 "
            "when covered defense information is required. "
            "Do not use the clause unless the requirement applies."
        ),
    )

    enriched = enrich_section(section)

    assert "covered defense information" in enriched.key_topics
    assert enriched.required_actions
    assert enriched.exceptions
    assert enriched.contracting_officer_notes

