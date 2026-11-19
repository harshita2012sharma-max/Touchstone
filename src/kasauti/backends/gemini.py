"""Backend for the Google Gemini API (REST, no SDK).

The key is sent in the ``x-goog-api-key`` header, never in the URL, so it
does not end up in logs or error messages that print URLs.
"""

from __future__ import annotations

from typing import Any

from kasauti.backends.base import Completion, HTTPBackend
from kasauti.config import GenerationSettings

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiBackend(HTTPBackend):
    """Calls ``models/{id}:generateContent`` on the Gemini API."""

    def __init__(self, *, api_key: str, base_url: str = GEMINI_BASE_URL, **kwargs: Any) -> None:
        """Create the backend with the key in a request header."""
        super().__init__(
            name="gemini",
            base_url=base_url,
            api_key=api_key,
            headers={"x-goog-api-key": api_key},
            **kwargs,
        )

    def _generate(self, model_id: str, prompt: str, settings: GenerationSettings) -> Completion:
        model_id = model_id.removeprefix("models/")
        data = self._request(
            "POST",
            f"/models/{model_id}:generateContent",
            model_id=model_id,
            json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": settings.temperature,
                    "topP": settings.top_p,
                    "maxOutputTokens": settings.max_tokens,
                    "seed": settings.seed,
                },
            },
        )
        candidates = data.get("candidates") or []
        if not candidates:
            block = (data.get("promptFeedback") or {}).get("blockReason")
            return Completion(text="", model_id=data.get("modelVersion"), finish_reason=block)
        first = candidates[0]
        parts = (first.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        return Completion(
            text=text,
            model_id=data.get("modelVersion"),
            finish_reason=first.get("finishReason"),
        )

    def list_models(self) -> list[str]:
        """Return ids of models that support ``generateContent``, following pagination."""
        ids: list[str] = []
        token: str | None = None
        while True:
            params: dict[str, str | int] = {"pageSize": 1000}
            if token:
                params["pageToken"] = token
            data = self._request("GET", "/models", params=params)
            for model in data.get("models", []):
                if "generateContent" in model.get("supportedGenerationMethods", []):
                    ids.append(str(model["name"]).removeprefix("models/"))
            token = data.get("nextPageToken")
            if not token:
                return sorted(ids)
