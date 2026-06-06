"""Local Ollama embedding client."""

import os

import httpx
from dotenv import load_dotenv

DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text:latest"


class OllamaEmbeddingClient:
    """Generate embeddings from a local Ollama model."""

    def __init__(self, host: str | None = None, model: str | None = None) -> None:
        """Initialize the embedding client.

        Args:
            host: Ollama host URL.
            model: Ollama embedding model name.
        """
        load_dotenv()
        self.host = (host or os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)).rstrip("/")
        self.model = model or os.getenv("OLLAMA_EMBED_MODEL", DEFAULT_OLLAMA_EMBED_MODEL)

    def embed(self, text: str) -> list[float]:
        """Embed a text string with Ollama.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.

        Raises:
            RuntimeError: If Ollama is unavailable or returns an invalid response.
        """
        try:
            response = httpx.post(
                f"{self.host}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=120,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama embedding request failed with status "
                f"{exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama embedding request failed: {exc}") from exc

        data = response.json()
        embedding = data.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise RuntimeError("Ollama response did not contain a valid embedding.")
        return [float(value) for value in embedding]

