"""Task interface and dataset loading.

A task knows how to load its items, turn an item into a prompt, and score a
model's reply. Data lives in ``kasauti/tasks/data/<task>.jsonl``, one JSON
object per line. Every shipped item must be original, CC-BY-4.0, and
reviewed by at least two people other than its author; this is enforced
when the data is loaded, so unreviewed items can never be scored.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from importlib.resources import files
from pathlib import Path
from typing import Any, ClassVar, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from kasauti.errors import KasautiError

MIN_REVIEWERS = 2


class DatasetError(KasautiError):
    """A dataset file is missing or has an invalid item."""


class ItemMeta(BaseModel):
    """Fields every dataset item must have: provenance, license and review."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[a-z0-9_]+-\d{3,}$")
    author: str = Field(min_length=1)
    license: Literal["CC-BY-4.0"]
    reviewers: list[str]
    notes: str | None = None

    @model_validator(mode="after")
    def _check_review(self) -> ItemMeta:
        if len(set(self.reviewers)) != len(self.reviewers):
            raise ValueError("reviewers must be different people")
        if self.author in self.reviewers:
            raise ValueError("the author cannot review their own item")
        if len(self.reviewers) < MIN_REVIEWERS:
            raise ValueError(
                f"each item needs at least {MIN_REVIEWERS} reviewers besides the author"
            )
        return self


S = TypeVar("S", bound=ItemMeta)


class ScoredOutput(BaseModel):
    """Score for one reply. ``unparsed`` means no answer could be read from it."""

    score: float = Field(ge=0.0, le=1.0)
    parsed: str | None = None
    unparsed: bool = False


class Task(ABC, Generic[S]):
    """Base class for all tasks. Subclasses set the class variables below."""

    name: ClassVar[str]
    version: ClassVar[str]
    description: ClassVar[str]
    sample_type: ClassVar[type[ItemMeta]]
    prompt_template: ClassVar[str]

    def __init__(self, data_path: str | Path | None = None) -> None:
        """Use the shipped data file unless ``data_path`` is given."""
        self._data_path = Path(data_path) if data_path is not None else None

    def _read_lines(self) -> list[str]:
        if self._data_path is not None:
            source: Any = self._data_path
        else:
            source = files("kasauti.tasks").joinpath("data").joinpath(f"{self.name}.jsonl")
        if not source.is_file():
            raise DatasetError(f"No data found for task '{self.name}' (looked for {source}).")
        text: str = source.read_text(encoding="utf-8")
        return text.splitlines()

    def load_samples(self, limit: int | None = None) -> list[S]:
        """Load and validate items in file order; return the first ``limit`` of them."""
        samples: list[S] = []
        seen: set[str] = set()
        for lineno, line in enumerate(self._read_lines(), start=1):
            if not line.strip():
                continue
            try:
                sample = self.sample_type.model_validate(json.loads(line))
            except (json.JSONDecodeError, ValidationError) as err:
                raise DatasetError(f"{self.name}: invalid item on line {lineno}: {err}") from err
            if not sample.id.startswith(f"{self.name}-"):
                raise DatasetError(
                    f"{self.name}: item id '{sample.id}' on line {lineno} must start "
                    f"with '{self.name}-'."
                )
            if sample.id in seen:
                raise DatasetError(f"{self.name}: duplicate id '{sample.id}' on line {lineno}.")
            seen.add(sample.id)
            samples.append(sample)  # type: ignore[arg-type]
        return samples[:limit] if limit is not None else samples

    @abstractmethod
    def build_prompt(self, sample: S) -> str:
        """Return the exact prompt sent to the model."""

    @abstractmethod
    def score(self, output: str, sample: S) -> ScoredOutput:
        """Score one reply between 0 and 1."""

    @abstractmethod
    def expected(self, sample: S) -> str | list[str]:
        """Return the reference answer(s), shown in reports."""
