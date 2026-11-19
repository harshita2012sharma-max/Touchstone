"""Model backends and the provider registry.

Every provider in :mod:`touchstone_llm.providers` gets a backend here. Each
user brings their own key. Third-party packages can add more providers through
the ``touchstone_llm.backends`` entry point group; each entry point must load
a callable that takes keyword overrides and returns a :class:`Backend`.

Default request rates are cautious guesses. Providers change their limits, so
pass ``requests_per_minute`` (``--rpm`` on the CLI) to override them.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from importlib.metadata import entry_points
from typing import Any

from touchstone_llm.backends.anthropic import AnthropicBackend
from touchstone_llm.backends.base import Backend, Completion
from touchstone_llm.backends.gemini import GeminiBackend
from touchstone_llm.backends.mock import MockBackend
from touchstone_llm.backends.openai_compat import OpenAICompatBackend
from touchstone_llm.env import custom_server, get_api_key
from touchstone_llm.errors import TouchstoneError
from touchstone_llm.providers import BY_NAME, CATALOG, ProviderInfo

__all__ = ["Backend", "Completion", "available_backends", "get_backend"]

BackendFactory = Callable[..., Backend]

DEFAULT_OLLAMA_URL = "http://localhost:11434"


def _required_key(name: str) -> str:
    key = get_api_key(name)
    assert key is not None  # get_api_key raises MissingAPIKeyError for keyed providers
    return key


def _build(info: ProviderInfo, **overrides: Any) -> Backend:
    options: dict[str, Any] = {"requests_per_minute": info.rpm, **overrides}
    if info.kind == "mock":
        return MockBackend()
    if info.kind == "gemini":
        return GeminiBackend(api_key=_required_key(info.name), **options)
    if info.kind == "anthropic":
        return AnthropicBackend(api_key=_required_key(info.name), **options)
    if info.kind == "ollama":
        base = os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).strip() or DEFAULT_OLLAMA_URL
        return OpenAICompatBackend(
            name="ollama",
            base_url=f"{base.rstrip('/')}/v1",
            api_key=None,
            connect_hint="Is Ollama running? Start it with `ollama serve`, then download a "
            "small model, e.g. `ollama pull <model>`.",
            **{"timeout": 300.0, **options},
        )
    if info.kind == "custom":
        url, key = custom_server()
        if not url:
            raise TouchstoneError(
                "No custom server address is set. In the web UI choose New test, then "
                "Custom server, and enter its address (for example "
                "https://api.example.com/v1), or set CUSTOM_BASE_URL."
            )
        return OpenAICompatBackend(
            name="custom",
            base_url=url,
            api_key=key,
            connect_hint=f"Could not reach {url}. Check the address and that it is running.",
            **{"timeout": 120.0, **options},
        )
    assert info.base_url is not None, info.name
    extra = {"X-Title": "touchstone"} if info.name == "openrouter" else None
    return OpenAICompatBackend(
        name=info.name,
        base_url=info.base_url,
        api_key=_required_key(info.name),
        extra_headers=extra,
        **options,
    )


def _plugins() -> dict[str, BackendFactory]:
    found: dict[str, BackendFactory] = {}
    for ep in entry_points(group="touchstone_llm.backends"):
        if ep.name not in BY_NAME:
            found[ep.name] = ep.load()
    return found


def available_backends() -> list[str]:
    """Names of all built-in providers (catalog order) followed by plugin providers."""
    plugins = sorted(ep.name for ep in entry_points(group="touchstone_llm.backends"))
    return [p.name for p in CATALOG] + [p for p in plugins if p not in BY_NAME]


def get_backend(provider: str, **overrides: Any) -> Backend:
    """Create the backend for ``provider``.

    Raises:
        TouchstoneError: unknown provider (the message lists known ones), or a
            custom server without an address.
        MissingAPIKeyError: the provider needs a key that is not set.

    """
    info = BY_NAME.get(provider)
    if info is not None:
        return _build(info, **overrides)
    plugin = _plugins().get(provider)
    if plugin is None:
        known = ", ".join(available_backends())
        raise TouchstoneError(f"Unknown provider '{provider}'. Available providers: {known}.")
    return plugin(**overrides)
