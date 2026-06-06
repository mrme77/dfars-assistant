"""Answer generation interface for OpenRouter-backed models."""

import os

import httpx
from dotenv import load_dotenv

DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash-lite-preview-09-2025"
DEFAULT_OPENROUTER_APP_TITLE = "DFARS App"
DEFAULT_OPENROUTER_REFERER = "http://127.0.0.1:8501"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def answer_with_openrouter(context: str) -> str:
    """Generate an answer from an OpenRouter chat model.

    Args:
        context: Fully assembled context package.

    Returns:
        Generated answer text.

    Raises:
        RuntimeError: If required environment variables are missing or the API fails.
    """
    load_dotenv()
    api_key = _load_openrouter_api_key()
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is required. Set it in `.env` or configure "
            "OPENROUTER_KEYCHAIN_SERVICE and OPENROUTER_KEYCHAIN_ACCOUNT."
        )

    try:
        response = httpx.post(
            OPENROUTER_URL,
            headers=_openrouter_headers(api_key),
            json={
                "model": DEFAULT_OPENROUTER_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": _system_prompt(),
                    },
                    {"role": "user", "content": context},
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"OpenRouter request failed with status {exc.response.status_code}: "
            f"{exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"OpenRouter request failed: {exc}") from exc

    data = response.json()
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("OpenRouter response did not contain an answer.") from exc


def _system_prompt() -> str:
    """Return the fixed behavior rules for DFARS answer generation."""
    return "\n".join(
        [
            "You are a DFARS research assistant.",
            "Answer only from the provided retrieved DFARS context.",
            "Cite DFARS section identifiers and page ranges for every substantive claim.",
            "If the excerpts do not answer the question, say so.",
            "Do not provide legal advice or final contract determinations.",
        ]
    )


def _openrouter_headers(api_key: str) -> dict[str, str]:
    """Build OpenRouter request headers with app attribution.

    Args:
        api_key: OpenRouter API key.

    Returns:
        Headers for the OpenRouter chat completion request.
    """
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": DEFAULT_OPENROUTER_APP_TITLE,
        "HTTP-Referer": DEFAULT_OPENROUTER_REFERER,
    }


def _load_openrouter_api_key() -> str | None:
    """Load the OpenRouter key from environment or macOS Keychain.

    Returns:
        API key string when configured, otherwise `None`.

    Raises:
        RuntimeError: If keychain lookup is configured but the keyring library fails.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        return api_key

    service = os.getenv("OPENROUTER_KEYCHAIN_SERVICE", "openrouter")
    account = os.getenv("OPENROUTER_KEYCHAIN_ACCOUNT", "OPENROUTER_API_KEY")
    if not service or not account:
        return None

    try:
        import keyring
    except ImportError as exc:
        raise RuntimeError(
            "The `keyring` package is required to read OPENROUTER_API_KEY "
            "from macOS Keychain. Install dependencies with "
            "`uv pip install -r requirements.txt --python dfars-env/bin/python`."
        ) from exc

    try:
        return keyring.get_password(service, account)
    except Exception as exc:
        raise RuntimeError(
            f"Could not read OpenRouter key from keychain service "
            f"`{service}` and account `{account}`."
        ) from exc
