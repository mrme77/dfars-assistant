"""Extract DFARS-style cross-references from section text."""

import re

SECTION_REFERENCE_PATTERN = re.compile(r"\b(?:\d{3}\.\d{3,4}(?:-\d{4})?|\d{3}\.\d{3})\b")


def extract_cross_references(text: str) -> list[str]:
    """Extract unique DFARS section references from text.

    Args:
        text: Source section text.

    Returns:
        Sorted unique section references.
    """
    return sorted(set(SECTION_REFERENCE_PATTERN.findall(text)))

