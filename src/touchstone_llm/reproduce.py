"""Compare a saved run with a fresh rerun of the same config.

Used by ``touchstone reproduce``: it checks that the prompts and settings are
byte-for-byte the same and shows how scores and outputs moved.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from touchstone_llm.results import RunResult


@dataclass
class TaskComparison:
    """Old vs new numbers for one task."""

    task: str
    old_score: float | None
    new_score: float | None
    changed_outputs: int = 0
    missing_samples: list[str] = field(default_factory=list)


@dataclass
class ReproduceReport:
    """Result of comparing two runs."""

    rows: list[TaskComparison]
    prompts_identical: bool
    settings_identical: bool


def compare_runs(old: RunResult, new: RunResult) -> ReproduceReport:
    """Compare prompts, settings, scores and outputs task by task."""
    new_tasks = {t.task: t for t in new.tasks}
    rows = []
    prompts_identical = True
    for old_task in old.tasks:
        new_task = new_tasks.get(old_task.task)
        if new_task is None:
            rows.append(TaskComparison(old_task.task, old_task.score, None))
            prompts_identical = False
            continue
        new_samples = {s.sample_id: s for s in new_task.samples}
        missing, changed = [], 0
        for sample in old_task.samples:
            other = new_samples.get(sample.sample_id)
            if other is None:
                missing.append(sample.sample_id)
                continue
            if other.prompt != sample.prompt:
                prompts_identical = False
            if other.output != sample.output:
                changed += 1
        if missing or old_task.prompt_template != new_task.prompt_template:
            prompts_identical = False
        rows.append(TaskComparison(old_task.task, old_task.score, new_task.score, changed, missing))
    return ReproduceReport(
        rows=rows,
        prompts_identical=prompts_identical,
        settings_identical=old.config.settings == new.config.settings,
    )
