"""Command-line search helper for validating DFARS retrieval."""

from pathlib import Path

from src.retrieval.hybrid_search import HybridSearcher
from src.retrieval.section_store import load_sections


def search_index(
    query: str,
    index_path: Path = Path("indexes/dfars_sections_enriched.jsonl"),
    use_vector: bool = False,
) -> None:
    """Print retrieval results for a query.

    Args:
        query: User search query.
        index_path: Section index path.
        use_vector: Whether to include local vector search.
    """
    sections = load_sections(index_path)
    searcher = HybridSearcher(sections, use_vector=use_vector)
    results = searcher.search(query)
    for result in results:
        section = result.section
        print(
            f"{section.section_id} | {section.title} | "
            f"pages {section.page_start}-{section.page_end} | "
            f"{result.retrieval_method} | {result.score:.2f}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search the DFARS section index.")
    parser.add_argument("query", help="Search query or exact DFARS section identifier.")
    parser.add_argument(
        "--vector",
        action="store_true",
        help="Include local vector search with Ollama/Chroma.",
    )
    args = parser.parse_args()
    search_index(args.query, use_vector=args.vector)
