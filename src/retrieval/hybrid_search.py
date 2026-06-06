"""Hybrid retrieval for DFARS questions."""

import re

from src.models import RetrievedSection, SectionRecord
from src.retrieval.keyword_search import KeywordSearcher
from src.retrieval.rerank import dedupe_results
from src.retrieval.section_store import SectionStore

SECTION_ID_PATTERN = re.compile(r"\b\d{3}\.\d{3,4}(?:-\d{4})?\b")


class HybridSearcher:
    """Retrieve DFARS sections using exact identifiers and BM25 search."""

    def __init__(self, sections: list[SectionRecord], use_vector: bool = True) -> None:
        """Initialize the hybrid searcher.

        Args:
            sections: Section records to search.
            use_vector: Whether to include semantic vector search.
        """
        self.store = SectionStore(sections)
        self.keyword_searcher = KeywordSearcher(sections)
        self.vector_searcher = _load_vector_searcher(sections) if use_vector else None

    def search(self, query: str, limit: int = 8) -> list[RetrievedSection]:
        """Search for relevant DFARS sections.

        Args:
            query: User question.
            limit: Maximum number of unique sections.

        Returns:
            Deduplicated retrieved sections.
        """
        exact_results = self._exact_results(query)
        keyword_results = self.keyword_searcher.search(query, limit=limit)
        vector_results = (
            self.vector_searcher.search(query, limit=limit)
            if self.vector_searcher is not None and _should_run_vector_search(query)
            else []
        )
        return dedupe_results([*exact_results, *keyword_results, *vector_results], limit=limit)

    def _exact_results(self, query: str) -> list[RetrievedSection]:
        """Retrieve exact section identifiers mentioned in a query."""
        results: list[RetrievedSection] = []
        for section_id in sorted(set(SECTION_ID_PATTERN.findall(query))):
            for section in self.store.exact_lookup(section_id):
                results.append(
                    RetrievedSection(
                        section=section,
                        score=1_000_000.0,
                        retrieval_method="exact",
                    )
                )
        return results


def _should_run_vector_search(query: str) -> bool:
    """Return whether semantic search should run for a query."""
    stripped = query.strip()
    exact_ids = SECTION_ID_PATTERN.findall(stripped)
    if exact_ids and SECTION_ID_PATTERN.sub("", stripped).strip() == "":
        return False
    return True


def _load_vector_searcher(sections: list[SectionRecord]):
    """Load vector search lazily so hosted BM25 mode avoids Chroma/Ollama imports."""
    from src.retrieval.vector_search import VectorSearcher

    return VectorSearcher(sections)
