"""Tests for the Ollama embedding client."""

from src.retrieval.ollama_embeddings import OllamaEmbeddingClient


def test_ollama_embedding_client_uses_env(monkeypatch) -> None:
    """It reads Ollama host and model from environment."""
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

    client = OllamaEmbeddingClient()

    assert client.host == "http://localhost:11434"
    assert client.model == "nomic-embed-text:latest"

