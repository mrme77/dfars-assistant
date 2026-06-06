"""Tests for OpenRouter answer configuration."""

import sys
from types import SimpleNamespace

import pytest

from src.generation.answer import (
    DEFAULT_OPENROUTER_MODEL,
    _openrouter_headers,
    _load_openrouter_api_key,
    answer_with_openrouter,
)


def test_default_openrouter_model_is_flash_lite_preview() -> None:
    """It uses the requested Gemini Flash Lite preview model by default."""
    assert DEFAULT_OPENROUTER_MODEL == "google/gemini-2.5-flash-lite-preview-09-2025"


def test_answer_requires_openrouter_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """It fails loudly when the OpenRouter API key is missing."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY is required"):
        answer_with_openrouter("context")


def test_load_openrouter_api_key_prefers_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It reads the OpenRouter key from the environment first."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")

    assert _load_openrouter_api_key() == "env-key"


def test_load_openrouter_api_key_falls_back_to_keychain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It reads the OpenRouter key from keychain when env is empty."""
    fake_keyring = SimpleNamespace(
        get_password=lambda service, account: f"{service}:{account}:key"
    )
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_KEYCHAIN_SERVICE", "openrouter")
    monkeypatch.setenv("OPENROUTER_KEYCHAIN_ACCOUNT", "OPENROUTER_API_KEY")
    monkeypatch.setitem(sys.modules, "keyring", fake_keyring)

    assert _load_openrouter_api_key() == "openrouter:OPENROUTER_API_KEY:key"


def test_openrouter_headers_include_app_title(monkeypatch: pytest.MonkeyPatch) -> None:
    """It sends OpenRouter attribution headers for tracking."""
    headers = _openrouter_headers("test-key")

    assert headers["X-Title"] == "DFARS App"
    assert headers["HTTP-Referer"] == "http://127.0.0.1:8501"
    assert headers["Authorization"] == "Bearer test-key"
