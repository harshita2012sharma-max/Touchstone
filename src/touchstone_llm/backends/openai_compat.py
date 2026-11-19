"""Backend for OpenAI-compatible chat APIs.

Groq, OpenRouter, OpenAI, Mistral, DeepSeek, xAI, Together, Hugging Face,
Ollama and most self-hosted servers accept the same ``/chat/completions`` and
``/models`` endpoints, so one class covers them; only the base URL and key differ.

Some models reject one of our fixed settings (for example certain OpenAI
models refuse ``temperature`` or want ``max_completion_tokens`` instead of
``max_tokens``). When the provider says so, the request is retried without
that setting, and a note is attached to every completion so the change is
recorded in the result instead of hidden.
"""

from __future__ import annotations

import re
from typing import Any

from touchstone_llm.backends.base import (
    AuthError,
    BackendError,
    Completion,
    HTTPBackend,
    RateLimitError,
    TransientError,
)
from touchstone_llm.config import GenerationSettings

_ADJUSTABLE = ("max_tokens", "temperature", "top_p", "seed")


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
        self._dropped: set[str] = set()
        self._max_completion_tokens = False
        self._notes: set[str] = set()

    def _body(self, model_id: str, prompt: str, settings: GenerationSettings) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.temperature,
            "top_p": settings.top_p,
            "max_tokens": settings.max_tokens,
            "seed": settings.seed,
        }
        if self._max_completion_tokens:
            body["max_completion_tokens"] = body.pop("max_tokens")
        for param in self._dropped:
            body.pop(param, None)
        return body

    def _adjust(self, message: str, body: dict[str, Any]) -> bool:
        """If the error names one of our settings, change the request; return True if changed."""
        lowered = message.lower()
        for param in _ADJUSTABLE:
            if param not in body or not re.search(rf"\b{param}\b", lowered):
                continue
            if param == "max_tokens" and "max_completion_tokens" in lowered:
                body["max_completion_tokens"] = body.pop("max_tokens")
                self._max_completion_tokens = True
                self._notes.add(f"{self.name}: sent max_completion_tokens instead of max_tokens")
            else:
                body.pop(param)
                self._dropped.add(param)
                self._notes.add(f"{self.name} rejected '{param}', so it was not sent")
            return True
        return False

    def _generate(self, model_id: str, prompt: str, settings: GenerationSettings) -> Completion:
        body = self._body(model_id, prompt, settings)
        for _ in range(len(_ADJUSTABLE) + 1):
            try:
                data = self._request("POST", "/chat/completions", model_id=model_id, json=body)
                break
            except (AuthError, RateLimitError, TransientError):
                raise
            except BackendError as err:
                if not self._adjust(str(err), body):
                    raise
        else:  # pragma: no cover - every adjustable setting was already removed
            raise BackendError(f"{self.name} kept rejecting the request.")
        choice = (data.get("choices") or [{}])[0]
        return Completion(
            text=(choice.get("message") or {}).get("content") or "",
            model_id=data.get("model"),
            finish_reason=choice.get("finish_reason"),
            notes=sorted(self._notes),
        )

    def list_models(self) -> list[str]:
        """Return the ids from ``GET /models``, sorted (handles list or ``{"data": [...]}``)."""
        data = self._request("GET", "/models")
        items = data if isinstance(data, list) else data.get("data", [])
        return sorted({str(m["id"]) for m in items if isinstance(m, dict) and "id" in m})
