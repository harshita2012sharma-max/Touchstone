"""Background eval jobs for the web UI.

Only one job runs at a time: free tiers are rate limited and the target
laptop is small. Progress is kept in memory; finished runs are saved to the
runs folder exactly like ``kasauti run`` does.
"""

from __future__ import annotations

import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from kasauti.backends.base import Backend
from kasauti.cache import ResponseCache
from kasauti.config import RunConfig
from kasauti.env import redact_secrets
from kasauti.errors import KasautiError
from kasauti.report import write_reports
from kasauti.runner import ProgressEvent, Runner

JobState = Literal["running", "done", "failed"]


class JobBusyError(KasautiError):
    """Another job is still running."""


@dataclass
class Job:
    """One background run and its progress."""

    id: str
    model: str
    state: JobState = "running"
    progress: dict[str, dict[str, int]] = field(default_factory=dict)
    run_id: str | None = None
    error: str | None = None

    def snapshot(self) -> dict[str, Any]:
        """JSON-safe copy of the current state."""
        return {
            "job_id": self.id,
            "model": self.model,
            "state": self.state,
            "progress": {k: dict(v) for k, v in self.progress.items()},
            "run_id": self.run_id,
            "error": self.error,
        }


class JobManager:
    """Starts jobs in a thread and tracks their state."""

    def __init__(self, runs_dir: Path, *, use_cache: bool = True) -> None:
        """Save finished runs into ``runs_dir``."""
        self._runs_dir = runs_dir
        self._use_cache = use_cache
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def get(self, job_id: str) -> dict[str, Any] | None:
        """Return a snapshot of a job, or ``None`` if unknown."""
        with self._lock:
            job = self._jobs.get(job_id)
            return job.snapshot() if job else None

    def start(self, config: RunConfig, backend: Backend) -> str:
        """Start a job; raise :class:`JobBusyError` if one is already running."""
        with self._lock:
            if any(j.state == "running" for j in self._jobs.values()):
                backend.close()
                raise JobBusyError("Another run is in progress. Wait for it to finish.")
            job = Job(id=secrets.token_hex(8), model=config.model)
            self._jobs[job.id] = job
        thread = threading.Thread(target=self._work, args=(job, config, backend), daemon=True)
        thread.start()
        return job.id

    def _on_event(self, job: Job) -> Callable[[ProgressEvent], None]:
        def handle(event: ProgressEvent) -> None:
            with self._lock:
                if event.kind == "task_start":
                    job.progress[event.task] = {"done": 0, "total": event.total}
                elif event.kind == "sample_done":
                    job.progress[event.task]["done"] = event.index

        return handle

    def _work(self, job: Job, config: RunConfig, backend: Backend) -> None:
        try:
            cache = ResponseCache() if self._use_cache else None
            result = Runner(
                config, backend=backend, cache=cache, on_event=self._on_event(job)
            ).run()
            result.save(self._runs_dir)
            write_reports(result, self._runs_dir)
            with self._lock:
                job.run_id = result.metadata.run_id
                job.state = "done"
        except KasautiError as err:
            self._fail(job, str(err))
        except Exception as err:
            self._fail(job, f"Unexpected error: {type(err).__name__}: {err}")
        finally:
            backend.close()

    def _fail(self, job: Job, message: str) -> None:
        with self._lock:
            job.error = redact_secrets(message)
            job.state = "failed"
