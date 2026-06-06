"""Local Ollama chat client for offline DFARS enrichment."""

import json
import os

import httpx
from dotenv import load_dotenv

DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_LLM_MODEL = "gemma4:26b"


class OllamaLLMClient:
    """Generate structured text from a local Ollama chat model."""

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        """Initialize the LLM client.

        Args:
            host: Ollama host URL.
            model: Ollama chat model name.
            timeout: Per-request timeout in seconds.
        """
        load_dotenv()
        self.host = (host or os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)).rstrip("/")
        self.model = model or os.getenv("OLLAMA_LLM_MODEL", DEFAULT_OLLAMA_LLM_MODEL)
        self.timeout = timeout

    def generate_json(self, prompt: str, system: str | None = None) -> dict:
        """Generate a JSON object from the model.

        Args:
            prompt: User prompt.
            system: Optional system instruction.

        Returns:
            Parsed JSON object from the model response.

        Raises:
            RuntimeError: If Ollama is unavailable or returns unparseable output.
        """
        payload: dict[str, object] = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.0},
        }
        if system:
            payload["system"] = system

        try:
            response = httpx.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama generate request failed with status "
                f"{exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama generate request failed: {exc}") from exc

        raw = response.json().get("response", "")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Ollama did not return valid JSON: {raw[:200]!r}"
            ) from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("Ollama JSON response was not an object.")
        return parsed
