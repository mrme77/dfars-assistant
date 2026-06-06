"""BM25 keyword retrieval over DFARS section records."""

from rank_bm25 import BM25Okapi

from src.models import RetrievedSection, SectionRecord


class KeywordSearcher:
    """BM25 keyword search over section summaries and original text."""

    def __init__(self, sections: list[SectionRecord]) -> None:
        """Initialize the searcher.

        Args:
            sections: Section records to search.
        """
        self.sections = sections
        self._tokens = [_tokenize(_search_text(section)) for section in sections]
        self._index = BM25Okapi(self._tokens)

    def search(self, query: str, limit: int = 5) -> list[RetrievedSection]:
        """Search sections by keyword relevance.

        Args:
            query: User query.
            limit: Maximum results.

        Returns:
            Ranked retrieved sections.
        """
        query_tokens = _tokenize(query)
        scores = self._index.get_scores(query_tokens)
        boosted_scores = [
            float(score) + _metadata_boost(query_tokens, section)
            for score, section in zip(scores, self.sections, strict=False)
        ]
        ranked = sorted(enumerate(boosted_scores), key=lambda item: item[1], reverse=True)
        return [
            RetrievedSection(
                section=self.sections[index],
                score=float(score),
                retrieval_method="bm25",
            )
            for index, score in ranked[:limit]
            if score > 0
        ]


def _search_text(section: SectionRecord) -> str:
    """Build searchable text for a section."""
    metadata_text = " ".join(
        [
            section.section_id,
            section.title,
            section.summary,
            " ".join(section.key_topics),
            " ".join(section.applies_when),
            " ".join(section.required_actions),
            " ".join(section.cross_references),
            " ".join(section.contracting_officer_notes),
        ]
    )
    return " ".join(
        [
            metadata_text,
            metadata_text,
            metadata_text,
            _trim_text(section.original_text, max_chars=4000),
        ]
    )


def _tokenize(text: str) -> list[str]:
    """Tokenize text for BM25 search."""
    import re

    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", text.lower())


def _trim_text(text: str, max_chars: int) -> str:
    """Trim long source text for keyword indexing."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _metadata_boost(query_tokens: list[str], section: SectionRecord) -> float:
    """Add deterministic relevance boosts for structured metadata matches."""
    query_set = set(query_tokens)
    metadata_tokens = _tokenize(
        " ".join(
            [
                section.section_id,
                section.title,
                " ".join(section.key_topics),
                " ".join(section.required_actions),
                " ".join(section.applies_when),
            ]
        )
    )
    if not metadata_tokens:
        return 0.0

    metadata_set = set(metadata_tokens)
    overlap = query_set & metadata_set
    phrase_boost = 0.0
    for topic in section.key_topics:
        topic_tokens = set(_tokenize(topic))
        if topic_tokens and topic_tokens <= query_set:
            phrase_boost += 8.0

    return (len(overlap) * 2.0) + phrase_boost
