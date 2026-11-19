"""Run configuration: which model, which tasks, and which generation settings.

Defaults are fixed (temperature 0, seed 42) so every model is tested the same
way and results can be reproduced.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_SEED = 42


class ModelRef(BaseModel):
    """A model address in the form ``provider/model-id``.

    Only the first ``/`` separates the provider, because some model ids
    (for example on OpenRouter) contain slashes themselves.
    """

    model_config = ConfigDict(frozen=True)

    provider: str
    model_id: str

    @classmethod
    def parse(cls, value: str) -> ModelRef:
        """Parse ``"provider/model-id"``; raise ``ValueError`` with a hint if malformed."""
        provider, sep, model_id = value.strip().partition("/")
        provider, model_id = provider.strip().lower(), model_id.strip()
        if not sep or not provider or not model_id:
            raise ValueError(
                f"Model must look like 'provider/model', for example 'groq/<model-id>'. "
                f"Got {value!r}. Run `kasauti list-models <provider>` to see available ids."
            )
        return cls(provider=provider, model_id=model_id)

    def __str__(self) -> str:
        """Return the ``provider/model-id`` form."""
        return f"{self.provider}/{self.model_id}"


class GenerationSettings(BaseModel):
    """Sampling settings sent to every backend. The same values apply to all models."""

    model_config = ConfigDict(frozen=True)

    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, gt=0.0, le=1.0)
    max_tokens: int = Field(default=512, ge=1, le=8192)
    seed: int = DEFAULT_SEED


class RunConfig(BaseModel):
    """Everything needed to start (and later reproduce) one eval run."""

    model_config = ConfigDict(frozen=True)

    model: str
    tasks: list[str] = Field(min_length=1)
    settings: GenerationSettings = Field(default_factory=GenerationSettings)
    limit: int | None = Field(default=None, ge=1, description="Max samples per task.")
    data_dir: str | None = Field(
        default=None, description="Folder with <task>.jsonl files; default is the shipped data."
    )
    allow_unreviewed: bool = Field(
        default=False, description="Accept items without two reviews (drafts only; never publish)."
    )

    @field_validator("model")
    @classmethod
    def _check_model(cls, value: str) -> str:
        return str(ModelRef.parse(value))

    @field_validator("tasks")
    @classmethod
    def _dedupe_tasks(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(t.strip() for t in value if t.strip()))

    @property
    def model_ref(self) -> ModelRef:
        """The parsed model address."""
        return ModelRef.parse(self.model)
