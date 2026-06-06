"""Build the local Chroma vector index for DFARS sections."""

from pathlib import Path

from src.retrieval.section_store import load_sections
from src.retrieval.vector_search import build_vector_index


def main() -> None:
    """Build the Chroma vector index from the best available section index."""
    source_path = _source_index_path()
    sections = load_sections(source_path)
    count = build_vector_index(sections)
    print(f"Embedded {count} DFARS sections from {source_path}.")


def _source_index_path() -> Path:
    """Choose enriched sections when available, otherwise base sections."""
    enriched_path = Path("indexes/dfars_sections_enriched.jsonl")
    if enriched_path.exists():
        return enriched_path
    return Path("indexes/dfars_sections.jsonl")


if __name__ == "__main__":
    main()
