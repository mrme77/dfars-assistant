"""Re-rank and deduplicate retrieved DFARS sections."""

from src.models import RetrievedSection


def dedupe_results(results: list[RetrievedSection], limit: int = 8) -> list[RetrievedSection]:
    """Deduplicate retrieved sections while preserving best score.

    Args:
        results: Candidate retrieval results.
        limit: Maximum number of unique records.

    Returns:
        Unique ranked section results.
    """
    best_by_section: dict[str, RetrievedSection] = {}
    for result in results:
        existing = best_by_section.get(result.section.section_id)
        if existing is None or result.score > existing.score:
            best_by_section[result.section.section_id] = result

    ranked = sorted(best_by_section.values(), key=lambda item: item.score, reverse=True)
    return ranked[:limit]

