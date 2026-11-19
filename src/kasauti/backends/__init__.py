"""Model backends and the provider registry.

Built-in providers: ``groq``, ``gemini``, ``openrouter``, ``ollama`` and the
offline ``mock``. Third-party packages can add more through the
``kasauti.backends`` entry point group; each entry point must load a
callable that takes keyword overrides and returns a :class:`Backend`.

Default request rates are cautious guesses for free tiers. Providers change
their limits, so pass ``requests_per_minute`` to override them.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from importlib.metadata import entry_points
from typing import Any

from kasauti.backends.base import Backend, Completion
from kasauti.backends.gemini import GeminiBackend
from kasauti.backends.mock import MockBackend
from kasauti.backends.openai_compat import OpenAICompatBackend
from kasauti.env import get_api_key
from kasauti.errors import KasautiError

__all__ = ["Backend", "Completion", "available_backends", "get_backend"]

BackendFactory = Callable[..., Backend]

DEFAULT_OLLAMA_URL = "http://localhost:11434"


def _groq(**overrides: Any) -> Backend:
    options: dict[str, Any] = {"requests_per_minute": 30, **overrides}
    return OpenAICompatBackend(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key=get_api_key("groq"),
        **options,
    )


def _openrouter(**overrides: Any) -> Backend:
    options: dict[str, Any] = {"requests_per_minute": 20, **overrides}
    return OpenAICompatBackend(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key=get_api_key("openrouter"),
        extra_headers={"X-Title": "kasauti"},
        **options,
    )


def _ollama(**overrides: Any) -> Backend:
    base = os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).strip() or DEFAULT_OLLAMA_URL
    options: dict[str, Any] = {"requests_per_minute": None, "timeout": 300.0, **overrides}
    return OpenAICompatBackend(
        name="ollama",
        base_url=f"{base.rstrip('/')}/v1",
        api_key=None,
        connect_hint="Is Ollama running? Start it with `ollama serve`, then pull a small "
        "model, e.g. `ollama pull <model>`.",
        **options,
    )


def _gemini(**overrides: Any) -> Backend:
    options: dict[str, Any] = {"requests_per_minute": 10, **overrides}
    key = get_api_key("gemini")
    assert key is not None  # gemini always needs a key; get_api_key raises otherwise
    return GeminiBackend(api_key=key, **options)


def _mock(**_overrides: Any) -> Backend:
    return MockBackend()


_BUILTINS: dict[str, BackendFactory] = {
    "groq": _groq,
    "gemini": _gemini,
    "openrouter": _openrouter,
    "ollama": _ollama,
    "mock": _mock,
}


def _plugins() -> dict[str, BackendFactory]:
    found: dict[str, BackendFactory] = {}
    for ep in entry_points(group="kasauti.backends"):
        if ep.name not in _BUILTINS:
            found[ep.name] = ep.load()
    return found


def available_backends() -> list[str]:
    """Names of all built-in and plugin providers, sorted."""
    return sorted({*_BUILTINS, *(ep.name for ep in entry_points(group="kasauti.backends"))})


def get_backend(provider: str, **overrides: Any) -> Backend:
    """Create the backend for ``provider``.

    Raises:
        KasautiError: unknown provider (the message lists known ones).
        MissingAPIKeyError: the provider needs a key that is not set.

    """
    factory = _BUILTINS.get(provider) or _plugins().get(provider)
    if factory is None:
        known = ", ".join(available_backends())
        raise KasautiError(f"Unknown provider '{provider}'. Available providers: {known}.")
    return factory(**overrides)
