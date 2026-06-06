"""Extract obligation-like sentences from DFARS text."""

import re

OBLIGATION_PATTERN = re.compile(r"\b(shall|must|required|requires|requirement)\b", re.IGNORECASE)


def extract_obligation_sentences(text: str) -> list[str]:
    """Return sentences that contain obligation language.

    Args:
        text: Source section text.

    Returns:
        Sentences containing obligation markers.
    """
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return [sentence for sentence in sentences if OBLIGATION_PATTERN.search(sentence)]

