"""Backend for OpenAI-compatible chat APIs: Groq, OpenRouter and Ollama.

All three accept the same ``/chat/completions`` and ``/models`` endpoints,
so one class covers them; only the base URL and key differ.
"""

from __future__ import annotations

from typing import Any

from touchstone_llm.backends.base import Completion, HTTPBackend
from touchstone_llm.config import GenerationSettings


class OpenAICompatBackend(HTTPBackend):
    """Talks to any server that implements the OpenAI chat completions API."""

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str | None,
        extra_headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Create the backend; adds a Bearer token when ``api_key`` is set."""
        headers = dict(extra_headers or {})
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        super().__init__(name=name, base_url=base_url, api_key=api_key, headers=headers, **kwargs)

    def _generate(self, model_id: str, prompt: str, settings: GenerationSettings) -> Completion:
        data = self._request(
            "POST",
            "/chat/completions",
            model_id=model_id,
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": settings.temperature,
                "top_p": settings.top_p,
                "max_tokens": settings.max_tokens,
                "seed": settings.seed,
            },
        )
        choice = (data.get("choices") or [{}])[0]
        return Completion(
            text=(choice.get("message") or {}).get("content") or "",
            model_id=data.get("model"),
            finish_reason=choice.get("finish_reason"),
        )

    def list_models(self) -> list[str]:
        """Return the ids from ``GET /models``, sorted."""
        data = self._request("GET", "/models")
        return sorted(str(m["id"]) for m in data.get("data", []) if "id" in m)
