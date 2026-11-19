"""Result data saved after every run.

A saved result holds everything needed to judge and reproduce it: the
model, date, settings, prompt templates, every prompt and output, and
the scores. API keys are never part of this data.
"""

from __future__ import annotations

import platform
import re
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from touchstone_llm import __version__
from touchstone_llm.config import RunConfig

SCHEMA_VERSION: Literal[1] = 1


class SampleResult(BaseModel):
    """One test item: what was asked, what the model said, and its score."""

    sample_id: str
    prompt: str
    output: str
    expected: str | list[str]
    score: float = Field(ge=0.0, le=1.0)
    parsed: str | None = None
    unparsed: bool = False
    error: str | None = None
    latency_ms: float | None = None


class TaskResult(BaseModel):
    """All samples for one task plus summary numbers."""

    task: str
    task_version: str
    prompt_template: str
    n: int
    score: float
    unparsed_rate: float
    errors: int
    samples: list[SampleResult]

    @classmethod
    def from_samples(
        cls,
        task: str,
        *,
        task_version: str,
        prompt_template: str,
        samples: list[SampleResult],
    ) -> TaskResult:
        """Build a task result and compute mean score, unparsed rate and error count."""
        n = len(samples)
        return cls(
            task=task,
            task_version=task_version,
            prompt_template=prompt_template,
            n=n,
            score=sum(s.score for s in samples) / n if n else 0.0,
            unparsed_rate=sum(s.unparsed for s in samples) / n if n else 0.0,
            errors=sum(s.error is not None for s in samples),
            samples=samples,
        )


def _git_sha() -> str | None:
    """Short git commit of the touchstone source, if running from a git checkout."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


class RunMetadata(BaseModel):
    """When, where and with which software version a run happened."""

    schema_version: Literal[1] = SCHEMA_VERSION
    run_id: str
    tool_version: str
    started_at: datetime
    finished_at: datetime | None = None
    provider_model_id: str | None = None
    python_version: str
    platform: str
    git_sha: str | None = None

    @classmethod
    def new(cls, config: RunConfig) -> RunMetadata:
        """Create metadata for a run that starts now."""
        now = datetime.now(timezone.utc)
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", config.model)[:60]
        return cls(
            run_id=f"{now:%Y%m%d-%H%M%S}-{slug}-{secrets.token_hex(3)}",
            tool_version=__version__,
            started_at=now,
            python_version=sys.version.split()[0],
            platform=platform.platform(terse=True),
            git_sha=_git_sha(),
        )


class RunResult(BaseModel):
    """A complete run: metadata, the exact config, and per-task results."""

    metadata: RunMetadata
    config: RunConfig
    tasks: list[TaskResult]

    def save(self, directory: str | Path) -> Path:
        """Write the result as readable UTF-8 JSON to ``directory/<run_id>.json``."""
        out_dir = Path(directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{self.metadata.run_id}.json"
        path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
        return path

    @classmethod
    def load(cls, path: str | Path) -> RunResult:
        """Read a result saved by :meth:`save`."""
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))
