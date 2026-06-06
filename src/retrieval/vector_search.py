"""Vector retrieval over DFARS section records with ChromaDB."""

from pathlib import Path
import os
import math

import chromadb
from dotenv import load_dotenv

from src.models import RetrievedSection, SectionRecord
from src.retrieval.ollama_embeddings import OllamaEmbeddingClient

DEFAULT_VECTOR_INDEX_PATH = Path("indexes/vector_index")
DEFAULT_COLLECTION_NAME = "dfars_sections"
DEFAULT_EMBED_MAX_CHARS = 6000


class VectorSearcher:
    """Semantic search interface for DFARS sections."""

    def __init__(
        self,
        sections: list[SectionRecord],
        index_path: Path = DEFAULT_VECTOR_INDEX_PATH,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        embedding_client: OllamaEmbeddingClient | None = None,
    ) -> None:
        """Initialize a semantic searcher.

        Args:
            sections: Section records to search.
            index_path: ChromaDB persistence path.
            collection_name: ChromaDB collection name.
            embedding_client: Local embedding client.
        """
        self.sections = sections
        self.embedding_client = embedding_client or OllamaEmbeddingClient()
        self._by_vector_id = {
            _vector_id(index, section): section
            for index, section in enumerate(sections)
        }
        self._client = chromadb.PersistentClient(path=str(index_path))
        self._collection = self._client.get_or_create_collection(collection_name)

    def search(self, query: str, limit: int = 5) -> list[RetrievedSection]:
        """Search semantically for relevant sections.

        Args:
            query: User query.
            limit: Maximum results.

        Returns:
            Ranked retrieved sections.
        """
        if self._collection.count() == 0:
            return []

        query_embedding = _normalize_vector(self.embedding_client.embed(query))
        response = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
        )
        ids = response.get("ids", [[]])[0]
        distances = response.get("distances", [[]])[0]
        results: list[RetrievedSection] = []
        for vector_id, distance in zip(ids, distances, strict=False):
            section = self._by_vector_id.get(str(vector_id))
            if section is None:
                continue
            results.append(
                RetrievedSection(
                    section=section,
                    score=_distance_to_score(float(distance)),
                    retrieval_method="vector",
                )
            )
        return results


def build_vector_index(
    sections: list[SectionRecord],
    index_path: Path = DEFAULT_VECTOR_INDEX_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding_client: OllamaEmbeddingClient | None = None,
) -> int:
    """Build or update the Chroma vector index for DFARS sections.

    Args:
        sections: Section records to embed.
        index_path: ChromaDB persistence path.
        collection_name: ChromaDB collection name.
        embedding_client: Local embedding client.

    Returns:
        Number of section embeddings upserted.
    """
    client = chromadb.PersistentClient(path=str(index_path))
    try:
        client.delete_collection(collection_name)
    except ValueError:
        pass
    collection = client.create_collection(collection_name)
    embedder = embedding_client or OllamaEmbeddingClient()

    for index, section in enumerate(sections):
        embedding_text = _embedding_text(section)
        collection.upsert(
            ids=[_vector_id(index, section)],
            embeddings=[_normalize_vector(embedder.embed(embedding_text))],
            documents=[embedding_text],
            metadatas=[
                {
                    "section_id": section.section_id,
                    "title": section.title,
                    "page_start": section.page_start,
                    "page_end": section.page_end,
                }
            ],
        )
    return len(sections)


def _embedding_text(section: SectionRecord) -> str:
    """Build text used for section embeddings."""
    load_dotenv()
    max_chars = int(os.getenv("OLLAMA_EMBED_MAX_CHARS", str(DEFAULT_EMBED_MAX_CHARS)))
    metadata_text = "\n".join(
        [
            f"DFARS {section.section_id}",
            f"Title: {section.title}",
            f"Summary: {section.summary}",
            f"Key topics: {', '.join(section.key_topics)}",
            f"Applies when: {'; '.join(section.applies_when)}",
            f"Required actions: {'; '.join(section.required_actions)}",
            f"Notes: {'; '.join(section.contracting_officer_notes)}",
            "Original text:",
        ]
    )
    remaining_chars = max(max_chars - len(metadata_text) - 1, 500)
    source_text = _middle_truncate(section.original_text, remaining_chars)
    return f"{metadata_text}\n{source_text}"


def _middle_truncate(text: str, max_chars: int) -> str:
    """Truncate long text while preserving the beginning and end.

    Args:
        text: Source text.
        max_chars: Maximum output characters.

    Returns:
        Truncated text.
    """
    if len(text) <= max_chars:
        return text
    head_length = max_chars * 2 // 3
    tail_length = max_chars - head_length
    return f"{text[:head_length]}\n...[truncated for embedding]...\n{text[-tail_length:]}"


def _distance_to_score(distance: float) -> float:
    """Convert a Chroma distance to a higher-is-better score."""
    return 50.0 / (1.0 + max(distance, 0.0))


def _normalize_vector(vector: list[float]) -> list[float]:
    """Return a unit-length vector for stable distance scoring."""
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _vector_id(index: int, section: SectionRecord) -> str:
    """Build a stable unique vector identifier for a section record."""
    return f"{index}:{section.section_id}"
