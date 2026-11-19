"""Run an eval: send every prompt to the model, score the replies, collect results.

Samples run one at a time, in file order. That is slow but kind to free-tier
rate limits and to an i3 laptop, and it makes runs reproducible. If any call
fails after retries, the whole run stops (no partial scores); replies so far
stay in the cache, so the same command resumes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from touchstone_llm.backends import get_backend
from touchstone_llm.backends.base import Backend, BackendError
from touchstone_llm.cache import ResponseCache, cache_key
from touchstone_llm.config import RunConfig
from touchstone_llm.errors import TouchstoneError
from touchstone_llm.results import RunMetadata, RunResult, SampleResult, TaskResult
from touchstone_llm.tasks import get_task
from touchstone_llm.tasks.base import DatasetError, ItemMeta, Task


class RunStopped(TouchstoneError):
    """A model call failed after retries, so the run was stopped."""


@dataclass(frozen=True)
class ProgressEvent:
    """Sent to ``on_event`` as the run progresses (used by the CLI and web UI)."""

    kind: Literal["task_start", "sample_done", "task_done"]
    task: str
    index: int = 0
    total: int = 0
    sample_id: str | None = None
    score: float | None = None
    cached: bool = False


class Runner:
    """Runs one :class:`RunConfig` against one backend."""

    def __init__(
        self,
        config: RunConfig,
        *,
        backend: Backend | None = None,
        cache: ResponseCache | None,
        on_event: Callable[[ProgressEvent], None] | None = None,
    ) -> None:
        """``backend`` defaults to the provider named in the config."""
        self.config = config
        self._backend = backend
        self._cache = cache
        self._emit = on_event or (lambda _event: None)

    def _load(self) -> list[tuple[Task[Any], list[ItemMeta]]]:
        """Load and validate every task before the first API call."""
        loaded = []
        for name in self.config.tasks:
            path = Path(self.config.data_dir) / f"{name}.jsonl" if self.config.data_dir else None
            task = get_task(name, data_path=path)
            samples = task.load_samples(
                self.config.limit, allow_unreviewed=self.config.allow_unreviewed
            )
            if not samples:
                raise DatasetError(f"Task '{name}' has no items to run.")
            loaded.append((task, samples))
        return loaded

    def run(self) -> RunResult:
        """Run all tasks and return the complete result."""
        metadata = RunMetadata.new(self.config)
        loaded = self._load()
        backend = self._backend or get_backend(self.config.model_ref.provider)
        model_ids: set[str] = set()
        try:
            task_results = [
                self._run_task(backend, task, samples, model_ids) for task, samples in loaded
            ]
        finally:
            if self._backend is None:
                backend.close()
        metadata = metadata.model_copy(
            update={
                "finished_at": datetime.now(timezone.utc),
                "provider_model_id": ", ".join(sorted(model_ids)) or None,
            }
        )
        return RunResult(metadata=metadata, config=self.config, tasks=task_results)

    def _run_task(
        self,
        backend: Backend,
        task: Task[Any],
        samples: list[ItemMeta],
        model_ids: set[str],
    ) -> TaskResult:
        total = len(samples)
        self._emit(ProgressEvent("task_start", task.name, total=total))
        results = []
        for index, sample in enumerate(samples, start=1):
            prompt = task.build_prompt(sample)
            key = cache_key(self.config.model, prompt, self.config.settings)
            completion = self._cache.get(key) if self._cache else None
            cached = completion is not None
            if completion is None:
                try:
                    completion = backend.generate(
                        self.config.model_ref.model_id, prompt, self.config.settings
                    )
                except BackendError as err:
                    hint = (
                        "Replies so far are cached; run the same command again to resume."
                        if self._cache
                        else "Run the command again to retry."
                    )
                    raise RunStopped(f"Run stopped at {sample.id}: {err}\n{hint}") from err
                if self._cache:
                    self._cache.put(key, completion)
            if completion.model_id:
                model_ids.add(completion.model_id)
            scored = task.score(completion.text, sample)
            results.append(
                SampleResult(
                    sample_id=sample.id,
                    prompt=prompt,
                    output=completion.text,
                    expected=task.expected(sample),
                    score=scored.score,
                    parsed=scored.parsed,
                    unparsed=scored.unparsed,
                    latency_ms=completion.latency_ms,
                )
            )
            self._emit(
                ProgressEvent(
                    "sample_done", task.name, index, total, sample.id, scored.score, cached
                )
            )
        result = TaskResult.from_samples(
            task.name,
            task_version=task.version,
            prompt_template=task.prompt_template,
            samples=results,
        )
        self._emit(ProgressEvent("task_done", task.name, total, total, score=result.score))
        return result
