"""Offline backend for tests and trying kasauti without any API key.

Models:
    ``mock/echo``: replies with the prompt itself.
    ``mock/fixed``: always replies ``"A"``.
Either can be given scripted ``replies`` keyed by the exact prompt.
"""

from __future__ import annotations

from kasauti.backends.base import Backend, Completion, ModelNotFoundError
from kasauti.config import GenerationSettings


class MockBackend(Backend):
    """Deterministic fake model. Makes no network calls."""

    name = "mock"
    MODELS = ("echo", "fixed")

    def __init__(self, replies: dict[str, str] | None = None) -> None:
        """Create the mock; ``replies`` maps exact prompts to scripted answers."""
        super().__init__(requests_per_minute=None, max_attempts=1)
        self._replies = dict(replies or {})

    def _generate(self, model_id: str, prompt: str, settings: GenerationSettings) -> Completion:
        if model_id not in self.MODELS:
            raise ModelNotFoundError(self.name, model_id)
        default = prompt if model_id == "echo" else "A"
        return Completion(
            text=self._replies.get(prompt, default),
            model_id=f"mock-{model_id}",
            finish_reason="stop",
        )

    def list_models(self) -> list[str]:
        """Return the two mock model ids."""
        return list(self.MODELS)
