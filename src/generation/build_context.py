"""Build isolated context packages for answer generation."""

from src.models import RetrievedSection

DEFAULT_CONTEXT_CHAR_BUDGET = 28000
MIN_SECTION_TEXT_CHARS = 600


def build_context_package(
    question: str,
    results: list[RetrievedSection],
    char_budget: int = DEFAULT_CONTEXT_CHAR_BUDGET,
) -> str:
    """Build model context from a question and retrieved sections.

    The total size of section original text is capped at `char_budget` so a
    single large section cannot blow the model context window. The budget is
    shared evenly across retrieved sections; metadata is always included.

    Args:
        question: User question.
        results: Retrieved DFARS sections.
        char_budget: Maximum characters of original text across all sections.

    Returns:
        Context string for the answer model.
    """
    per_section_budget = _per_section_budget(len(results), char_budget)

    section_blocks = [
        _format_section(result, per_section_budget) for result in results
    ]

    return "\n\n".join(
        [
            "User Question:",
            question,
            "Retrieved DFARS Sections:",
            "\n\n---\n\n".join(section_blocks),
        ]
    )


def _per_section_budget(section_count: int, char_budget: int) -> int:
    """Return the original-text char allowance for each section."""
    if section_count <= 0:
        return char_budget
    return max(MIN_SECTION_TEXT_CHARS, char_budget // section_count)


def _format_section(result: RetrievedSection, text_budget: int) -> str:
    """Format one retrieved section with metadata and trimmed source text."""
    section = result.section
    lines = [
        f"Section: DFARS {section.section_id}",
        f"Title: {section.title}",
        f"Pages: {section.page_start}-{section.page_end}",
        f"Summary: {section.summary}",
    ]
    lines.extend(_metadata_lines(section))
    lines.append("Original Text:")
    lines.append(_trim(section.original_text, text_budget))
    return "\n".join(lines)


def _metadata_lines(section) -> list[str]:
    """Render non-empty enriched metadata as labeled lines."""
    lines: list[str] = []
    if section.key_topics:
        lines.append(f"Key Topics: {', '.join(section.key_topics)}")
    if section.applies_when:
        lines.append("Applies When:")
        lines.extend(f"  - {item}" for item in section.applies_when)
    if section.required_actions:
        lines.append("Required Actions:")
        lines.extend(f"  - {item}" for item in section.required_actions)
    if section.exceptions:
        lines.append("Exceptions:")
        lines.extend(f"  - {item}" for item in section.exceptions)
    if section.cross_references:
        lines.append(f"Cross References: {', '.join(section.cross_references)}")
    return lines


def _trim(text: str, max_chars: int) -> str:
    """Trim original text to the budget, marking truncation."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n[... section text truncated for context budget ...]"
