"""Errors raised by model backends."""

from __future__ import annotations

from kasauti.errors import KasautiError


class BackendError(KasautiError):
    """A model provider call failed in a way that retrying will not fix."""


class AuthError(BackendError):
    """The provider rejected the API key."""


class ModelNotFoundError(BackendError):
    """The model id is unknown, misspelled or retired."""

    def __init__(self, provider: str, model_id: str, detail: str = "") -> None:
        """Explain that the id may be retired and how to list current ids."""
        msg = (
            f"Model '{model_id}' is not available on {provider} "
            f"(it may be retired or misspelled).\n"
            f"Run `kasauti list-models {provider}` to see current model ids."
        )
        if detail:
            msg += f"\nProvider said: {detail}"
        super().__init__(msg)


class RateLimitError(BackendError):
    """The provider asked us to slow down (HTTP 429). Retryable."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        """Store the provider's suggested wait in seconds, if it sent one."""
        super().__init__(message)
        self.retry_after = retry_after


class TransientError(BackendError):
    """A temporary failure (server error, timeout). Retryable."""
