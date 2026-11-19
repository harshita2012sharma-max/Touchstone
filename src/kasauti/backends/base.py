"""Backend interface shared by every model provider.

To add a provider, subclass :class:`Backend` (or :class:`HTTPBackend`),
implement ``_generate`` and ``list_models``, and register a factory (see
``kasauti.backends``).
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import httpx
from pydantic import BaseModel

from kasauti import __version__
from kasauti.backends.errors import (
    AuthError,
    BackendError,
    ModelNotFoundError,
    RateLimitError,
    TransientError,
)
from kasauti.backends.ratelimit import RateLimiter, with_retries
from kasauti.config import GenerationSettings
from kasauti.env import PROVIDER_KEYS, redact_secrets

__all__ = [
    "AuthError",
    "Backend",
    "BackendError",
    "Completion",
    "HTTPBackend",
    "ModelNotFoundError",
    "RateLimitError",
    "TransientError",
]

_MODEL_MISSING_HINTS = (
    "model_not_found",
    "does not exist",
    "decommissioned",
    "not a valid model",
    "not found",
    "no endpoints found",
    "is not supported",
)


class Completion(BaseModel):
    """A model's reply to one prompt."""

    text: str
    model_id: str | None = None
    """Exact model id or version the provider reports, if any."""
    finish_reason: str | None = None
    latency_ms: float = 0.0


class Backend(ABC):
    """Base class: adds rate limiting, retries and timing around ``_generate``."""

    name: str

    def __init__(
        self,
        *,
        requests_per_minute: float | None,
        max_attempts: int = 5,
        base_delay: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Set up the rate limiter and retry policy."""
        self._limiter = RateLimiter(requests_per_minute, clock=clock, sleep=sleep)
        self._max_attempts = max_attempts
        self._base_delay = base_delay
        self._sleep = sleep
        self._clock = clock

    def generate(self, model_id: str, prompt: str, settings: GenerationSettings) -> Completion:
        """Send one prompt and return the reply, retrying temporary failures."""

        def attempt() -> Completion:
            self._limiter.acquire()
            start = self._clock()
            completion = self._generate(model_id, prompt, settings)
            elapsed = (self._clock() - start) * 1000
            return completion.model_copy(update={"latency_ms": max(elapsed, 0.0)})

        return with_retries(
            attempt,
            max_attempts=self._max_attempts,
            base_delay=self._base_delay,
            sleep=self._sleep,
        )

    @abstractmethod
    def _generate(self, model_id: str, prompt: str, settings: GenerationSettings) -> Completion:
        """Make exactly one provider call."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return model ids the provider currently offers, sorted."""

    def close(self) -> None:  # noqa: B027  (optional hook, default does nothing)
        """Release network resources."""


class HTTPBackend(Backend):
    """A backend that talks to a JSON HTTP API with ``httpx``."""

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str | None,
        headers: dict[str, str] | None = None,
        timeout: float = 60.0,
        connect_hint: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Create the HTTP client. ``connect_hint`` is shown when the server is unreachable."""
        super().__init__(**kwargs)
        self.name = name
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._connect_hint = connect_hint
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"User-Agent": f"kasauti/{__version__}", **(headers or {})},
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the HTTP connection pool."""
        self._client.close()

    def _redact(self, text: str) -> str:
        text = redact_secrets(text)
        if self._api_key:
            text = text.replace(self._api_key, "***")
        return text

    def _request(self, method: str, path: str, model_id: str = "", **kwargs: Any) -> Any:
        """Send a request and return parsed JSON, mapping failures to backend errors."""
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.ConnectError as err:
            hint = f"\n{self._connect_hint}" if self._connect_hint else ""
            raise BackendError(
                f"Could not connect to {self.name} at {self.base_url}.{hint}"
            ) from err
        except httpx.TransportError as err:
            raise TransientError(f"Network problem talking to {self.name}: {err}") from err
        if response.is_success:
            return response.json()
        self._raise_for_status(response, model_id)

    def _raise_for_status(self, response: httpx.Response, model_id: str) -> None:
        status = response.status_code
        detail = self._redact(_error_detail(response))
        lowered = detail.lower()
        if status in (401, 403) or "api key not valid" in lowered or "api_key_invalid" in lowered:
            key = PROVIDER_KEYS.get(self.name)
            where = f" Check {key.env_var} in your .env file." if key else ""
            raise AuthError(f"{self.name} rejected the API key (HTTP {status}).{where}")
        if status == 429:
            raise RateLimitError(
                f"{self.name} rate limit reached (HTTP 429). {detail}".strip(),
                retry_after=_retry_after(response),
            )
        if status >= 500:
            raise TransientError(f"{self.name} server error (HTTP {status}). {detail}".strip())
        if status == 404 or (status == 400 and any(h in lowered for h in _MODEL_MISSING_HINTS)):
            raise ModelNotFoundError(self.name, model_id, detail)
        raise BackendError(f"{self.name} returned HTTP {status}. {detail}".strip())


def _error_detail(response: httpx.Response) -> str:
    """Best-effort error text from a provider's JSON error body."""
    try:
        data = response.json()
    except ValueError:
        return response.text[:300]
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            parts = [str(error.get("message", "")), str(error.get("code", ""))]
            parts += [
                str(d.get("reason", "")) for d in error.get("details", []) if isinstance(d, dict)
            ]
            return " ".join(p for p in parts if p and p != "None")
        if isinstance(error, str):
            return error
    return ""


def _retry_after(response: httpx.Response) -> float | None:
    value = response.headers.get("retry-after")
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None
