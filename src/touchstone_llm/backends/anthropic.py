"""Backend for Anthropic's Messages API (Claude models).

Anthropic does not accept a ``seed``, and recent models do not allow
``temperature`` and ``top_p`` together, so only ``temperature`` is sent.
Both facts are recorded as notes on every completion.
"""

from __future__ import annotations

from typing import Any

from touchstone_llm.backends.base import Completion, HTTPBackend
from touchstone_llm.config import GenerationSettings

ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"
_NOTES = ["anthropic: seed and top_p are not sent (not supported together with temperature)"]


class AnthropicBackend(HTTPBackend):
    """Calls ``POST /messages`` with an ``x-api-key`` header."""

    def __init__(self, *, api_key: str, base_url: str = ANTHROPIC_BASE_URL, **kwargs: Any) -> None:
        """Create the backend with the key in a request header."""
        super().__init__(
            name="anthropic",
            base_url=base_url,
            api_key=api_key,
            headers={"x-api-key": api_key, "anthropic-version": ANTHROPIC_VERSION},
            **kwargs,
        )

    def _generate(self, model_id: str, prompt: str, settings: GenerationSettings) -> Completion:
        data = self._request(
            "POST",
            "/messages",
            model_id=model_id,
            json={
                "model": model_id,
                "max_tokens": settings.max_tokens,
                "temperature": settings.temperature,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        blocks = data.get("content") or []
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        return Completion(
            text=text,
            model_id=data.get("model"),
            finish_reason=data.get("stop_reason"),
            notes=list(_NOTES),
        )

    def list_models(self) -> list[str]:
        """Return model ids from ``GET /models``, following pagination."""
        ids: list[str] = []
        after: str | None = None
        while True:
            params: dict[str, str | int] = {"limit": 1000}
            if after:
                params["after_id"] = after
            data = self._request("GET", "/models", params=params)
            ids += [str(m["id"]) for m in data.get("data", []) if "id" in m]
            if not data.get("has_more") or not data.get("last_id"):
                return sorted(ids)
            after = str(data["last_id"])
