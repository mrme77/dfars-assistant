"""Tests for DFARS section heading detection."""

from src.ingestion.detect_sections import detect_section_heading


def test_detects_standard_section_heading() -> None:
    """It detects a normal DFARS section heading."""
    result = detect_section_heading("204.7302 Policy.")

    assert result == ("204.7302", "Policy.")


def test_detects_clause_heading() -> None:
    """It detects a DFARS clause heading."""
    result = detect_section_heading("252.204-7012 Safeguarding Covered Defense Information.")

    assert result == (
        "252.204-7012",
        "Safeguarding Covered Defense Information.",
    )


def test_returns_none_for_body_text() -> None:
    """It ignores body text that is not a section heading."""
    result = detect_section_heading("The contractor shall provide adequate security.")

    assert result is None


def test_returns_none_for_cross_reference_body_line() -> None:
    """It ignores body text that starts with a DFARS reference."""
    result = detect_section_heading("252.232-7003 unless one of the exceptions applies.")

    assert result is None
