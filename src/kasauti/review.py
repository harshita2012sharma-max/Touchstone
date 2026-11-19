"""Dataset review workflow for maintainers (not needed to run evals).

New items start in ``datasets/pending/<task>.jsonl`` with no reviewers and are
never scored. The workflow:

1. ``python -m kasauti.review check``: validate every pending item.
2. ``python -m kasauti.review export review.csv``: a sheet reviewers can
   open in Excel or Google Sheets. They fill ``verdict`` (ok / fix / reject)
   and ``comment``.
3. ``python -m kasauti.review import review_rev1.csv --reviewer rev1``:
   records each "ok" as an approval by that reviewer and prints feedback.
4. ``python -m kasauti.review promote``: moves items approved by at least
   two reviewers (not the author) into the shipped data.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError

from kasauti.tasks import available_tasks, get_task
from kasauti.tasks.base import MIN_REVIEWERS, PLACEHOLDER_REVIEWERS, DatasetError, ItemMeta, Task

DEFAULT_PENDING = Path("datasets/pending")
CSV_FIELDS = ["id", "task", "prompt", "expected", "verdict", "comment"]
OK_VERDICTS = {"ok", "yes", "approve", "approved"}
OTHER_VERDICTS = {"fix", "reject", ""}


def default_shipped_dir() -> Path:
    """Folder of the shipped task data inside the source tree."""
    return Path(str(files("kasauti.tasks").joinpath("data")))


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    items = []
    for lineno, line in enumerate(path.read_text("utf-8").splitlines(), start=1):
        if line.strip():
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as err:
                raise DatasetError(f"{path}: bad JSON on line {lineno}: {err}") from err
    return items


def _write(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), "utf-8")


def _task_files(pending_dir: Path) -> dict[str, Path]:
    known = set(available_tasks())
    found = {}
    for path in sorted(pending_dir.glob("*.jsonl")):
        if path.stem not in known:
            raise DatasetError(f"{path.name}: '{path.stem}' is not a known task name.")
        found[path.stem] = path
    return found


def _validate_content(task: Task[Any], item: dict[str, Any]) -> ItemMeta:
    """Validate everything except the review count (pending items lack reviewers)."""
    trial = {**item, "reviewers": PLACEHOLDER_REVIEWERS}
    try:
        sample = task.sample_type.model_validate(trial)
    except ValidationError as err:
        raise DatasetError(f"{item.get('id', '<no id>')}: {err}") from err
    if not sample.id.startswith(f"{task.name}-"):
        raise DatasetError(f"{sample.id}: id must start with '{task.name}-'.")
    return sample


def check_pending(pending_dir: Path) -> dict[str, int]:
    """Validate all pending items; return item counts per task."""
    counts = {}
    for name, path in _task_files(pending_dir).items():
        task = get_task(name)
        items = _read(path)
        ids = [str(i.get("id")) for i in items]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise DatasetError(f"{path.name}: duplicate ids {sorted(dupes)}")
        for item in items:
            _validate_content(task, item)
        counts[name] = len(items)
    return counts


def export_csv(pending_dir: Path, out_path: Path) -> int:
    """Write a review sheet with the exact prompt and expected answer per item."""
    rows = []
    for name, path in _task_files(pending_dir).items():
        task = get_task(name)
        for item in _read(path):
            sample = _validate_content(task, item)
            expected = task.expected(sample)
            rows.append(
                {
                    "id": sample.id,
                    "task": name,
                    "prompt": task.build_prompt(sample),
                    "expected": " | ".join(expected) if isinstance(expected, list) else expected,
                    "verdict": "",
                    "comment": "",
                }
            )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


@dataclass
class ImportSummary:
    """What an imported review sheet changed."""

    approved: list[str] = field(default_factory=list)
    feedback: list[tuple[str, str, str]] = field(default_factory=list)


def import_csv(pending_dir: Path, csv_path: Path, reviewer: str) -> ImportSummary:
    """Record ``reviewer``'s "ok" verdicts; collect fix/reject comments."""
    reviewer = reviewer.strip()
    if not reviewer:
        raise DatasetError("Reviewer name must not be empty.")
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    verdicts: dict[str, tuple[str, str]] = {}
    for row in rows:
        verdict = (row.get("verdict") or "").strip().lower()
        if verdict not in OK_VERDICTS | OTHER_VERDICTS:
            raise DatasetError(
                f"{row.get('id')}: unknown verdict '{verdict}'. Use ok, fix or reject."
            )
        verdicts[row["id"]] = (verdict, (row.get("comment") or "").strip())

    summary = ImportSummary()
    for path in _task_files(pending_dir).values():
        items = _read(path)
        for item in items:
            verdict, comment = verdicts.get(item["id"], ("", ""))
            if verdict in OK_VERDICTS:
                if item["author"] == reviewer:
                    raise DatasetError(f"{item['id']}: the author cannot review their own item.")
                if reviewer not in item["reviewers"]:
                    item["reviewers"].append(reviewer)
                summary.approved.append(item["id"])
            elif verdict:
                summary.feedback.append((item["id"], verdict, comment))
        _write(path, items)
    return summary


def promote(pending_dir: Path, shipped_dir: Path) -> dict[str, int]:
    """Move items with enough independent approvals into the shipped data."""
    moved: dict[str, int] = {}
    for name, path in _task_files(pending_dir).items():
        task = get_task(name)
        shipped_path = shipped_dir / f"{name}.jsonl"
        shipped = _read(shipped_path)
        shipped_ids = {i["id"] for i in shipped}
        keep, ready = [], []
        for item in _read(path):
            if len(item.get("reviewers", [])) >= MIN_REVIEWERS:
                if item["id"] in shipped_ids:
                    raise DatasetError(f"{item['id']} is already shipped; give it a new id.")
                try:
                    task.sample_type.model_validate(item)
                except ValidationError as err:
                    raise DatasetError(f"{item['id']}: {err}") from err
                ready.append(item)
            else:
                keep.append(item)
        if ready:
            _write(shipped_path, shipped + ready)
            _write(path, keep)
            moved[name] = len(ready)
    return moved


app = typer.Typer(help="Dataset review workflow for kasauti maintainers.", add_completion=False)


@app.command("check")
def _check_cmd(pending: Path = typer.Option(DEFAULT_PENDING, help="Pending items folder.")) -> None:
    """Validate pending items."""
    for name, n in check_pending(pending).items():
        typer.echo(f"{name}: {n} pending item(s) OK")


@app.command("export")
def _export_cmd(
    out: Path = typer.Argument(..., help="CSV file to write."),
    pending: Path = typer.Option(DEFAULT_PENDING, help="Pending items folder."),
) -> None:
    """Write a review sheet (open it in Excel or Google Sheets)."""
    typer.echo(f"Wrote {export_csv(pending, out)} item(s) to {out}")


@app.command("import")
def _import_cmd(
    sheet: Path = typer.Argument(..., help="Filled review CSV."),
    reviewer: str = typer.Option(..., help="Reviewer's name or GitHub handle."),
    pending: Path = typer.Option(DEFAULT_PENDING, help="Pending items folder."),
) -> None:
    """Record a reviewer's verdicts."""
    summary = import_csv(pending, sheet, reviewer)
    typer.echo(f"{reviewer} approved {len(summary.approved)} item(s).")
    for item_id, verdict, comment in summary.feedback:
        typer.echo(f"  {verdict.upper():6} {item_id}: {comment or '(no comment)'}")


@app.command("promote")
def _promote_cmd(
    pending: Path = typer.Option(DEFAULT_PENDING, help="Pending items folder."),
) -> None:
    """Move fully reviewed items into the shipped data."""
    moved = promote(pending, default_shipped_dir())
    typer.echo(
        "\n".join(f"{k}: {v} item(s) promoted" for k, v in moved.items()) or "Nothing ready."
    )


if __name__ == "__main__":
    app()
