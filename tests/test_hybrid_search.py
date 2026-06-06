"""Tests for hybrid DFARS retrieval."""

from src.models import SectionRecord
from src.retrieval.hybrid_search import HybridSearcher, _should_run_vector_search


def test_exact_identifier_result_ranks_first() -> None:
    """It prioritizes exact DFARS identifier matches."""
    sections = [
        SectionRecord(
            section_id="204.7302",
            title="Policy.",
            page_start=1,
            page_end=1,
            original_text="Cyber incident reporting policy.",
        ),
        SectionRecord(
            section_id="252.204-7012",
            title="Safeguarding Covered Defense Information.",
            page_start=2,
            page_end=4,
            original_text="Covered defense information and cyber incident reporting.",
        ),
    ]
    searcher = HybridSearcher(sections)

    results = searcher.search("What does 252.204-7012 require?")

    assert results[0].section.section_id == "252.204-7012"
    assert results[0].retrieval_method == "exact"


def test_exact_identifier_only_query_skips_vector_search() -> None:
    """It avoids semantic search for pure section ID lookups."""
    assert not _should_run_vector_search("252.204-7012")


def test_natural_language_query_runs_vector_search() -> None:
    """It uses semantic search when the query includes natural language."""
    assert _should_run_vector_search("What does 252.204-7012 require?")


def test_bm25_finds_cyber_clause_without_vector_search() -> None:
    """It can retrieve cyber clauses in hosted BM25-only mode."""
    sections = [
        SectionRecord(
            section_id="252.204-7012",
            title="Safeguarding Covered Defense Information.",
            page_start=1,
            page_end=2,
            original_text="Cyber incident reporting for covered defense information.",
            key_topics=["cybersecurity", "covered defense information"],
            required_actions=["Include the clause when covered defense information is required."],
        ),
        SectionRecord(
            section_id="212.371",
            title="Commercial products.",
            page_start=3,
            page_end=4,
            original_text="Commercial acquisition clauses and provisions.",
        ),
    ]
    searcher = HybridSearcher(sections, use_vector=False)

    results = searcher.search(
        "what cybersecurity clauses should I include for covered defense information"
    )

    assert results[0].section.section_id == "252.204-7012"
