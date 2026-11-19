"""Command-line interface: ``kasauti run``, ``list-tasks``, ``list-models``."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from kasauti import __version__
from kasauti.backends import available_backends, get_backend
from kasauti.cache import ResponseCache
from kasauti.config import GenerationSettings, RunConfig
from kasauti.env import load_env, redact_secrets
from kasauti.errors import KasautiError
from kasauti.results import RunResult
from kasauti.runner import ProgressEvent, Runner
from kasauti.tasks import available_tasks, get_task
from kasauti.tasks.base import DatasetError

app = typer.Typer(
    name="kasauti",
    help="A touchstone for LLMs in Hindi and Hinglish.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console(highlight=False)


def _fail(message: str) -> typer.Exit:
    """Print a clean, redacted error (no traceback) and return an exit to raise."""
    console.print(Text(f"Error: {redact_secrets(message)}", style="bold red"))
    return typer.Exit(code=1)


def _validation_message(err: ValidationError) -> str:
    return "; ".join(str(e["msg"]).removeprefix("Value error, ") for e in err.errors())


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"kasauti {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the installed kasauti version and exit.",
        callback=_print_version,
        is_eager=True,
    ),
) -> None:
    """Run small, reproducible LLM evals in Hindi and Hinglish."""


@app.command()
def run(
    model: str = typer.Option(
        ..., "--model", "-m", help="provider/model-id. See `kasauti list-models <provider>`."
    ),
    tasks: str = typer.Option(
        ..., "--tasks", "-t", help="Comma-separated task names, or 'all'. See `list-tasks`."
    ),
    limit: int | None = typer.Option(None, min=1, help="Use only the first N items per task."),
    max_tokens: int = typer.Option(512, min=1, max=8192, help="Max reply length in tokens."),
    rpm: float | None = typer.Option(None, min=0.1, help="Override requests per minute."),
    output_dir: Path = typer.Option(Path("runs"), help="Where to save the result JSON."),
    data_dir: Path | None = typer.Option(None, help="Use <task>.jsonl files from this folder."),
    allow_unreviewed: bool = typer.Option(
        False, help="Accept items without two reviews (for trying drafts; never publish)."
    ),
    no_cache: bool = typer.Option(False, "--no-cache", help="Ignore cached replies."),
    env_file: Path | None = typer.Option(None, help="Path to a .env file with API keys."),
) -> None:
    """Run tasks against a model and print a score table.

    Temperature (0) and seed (42) are fixed so every model is tested the same way.
    """
    load_env(env_file)
    names = available_tasks() if tasks.strip().lower() == "all" else tasks.split(",")
    try:
        config = RunConfig(
            model=model,
            tasks=names,
            limit=limit,
            settings=GenerationSettings(max_tokens=max_tokens),
            data_dir=str(data_dir) if data_dir else None,
            allow_unreviewed=allow_unreviewed,
        )
    except ValidationError as err:
        raise _fail(_validation_message(err)) from None

    try:
        overrides = {"requests_per_minute": rpm} if rpm else {}
        backend = get_backend(config.model_ref.provider, **overrides)
        cache = None if no_cache else ResponseCache()
        with Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            bars: dict[str, TaskID] = {}

            def on_event(event: ProgressEvent) -> None:
                if event.kind == "task_start":
                    bars[event.task] = progress.add_task(event.task, total=event.total)
                elif event.kind == "sample_done":
                    progress.update(bars[event.task], completed=event.index)

            try:
                result = Runner(config, backend=backend, cache=cache, on_event=on_event).run()
            finally:
                backend.close()
        path = result.save(output_dir)
    except KasautiError as err:
        raise _fail(str(err)) from None
    except KeyboardInterrupt:
        raise _fail("Stopped by user. Cached replies are kept; run again to resume.") from None

    _print_summary(result, path)


def _print_summary(result: RunResult, path: Path) -> None:
    meta, cfg = result.metadata, result.config
    table = Table(title=f"kasauti results: {cfg.model}", title_justify="left")
    table.add_column("Task")
    table.add_column("n", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Unparsed", justify="right")
    table.add_column("Avg latency", justify="right")
    for t in result.tasks:
        latencies = [s.latency_ms for s in t.samples if s.latency_ms]
        avg = f"{sum(latencies) / len(latencies) / 1000:.1f}s" if latencies else "-"
        table.add_row(t.task, str(t.n), f"{t.score:.1%}", f"{t.unparsed_rate:.0%}", avg)
    console.print(table)
    s = cfg.settings
    console.print(
        Text(
            f"Model id reported: {meta.provider_model_id or 'not reported'}\n"
            f"Date (UTC): {meta.started_at:%Y-%m-%d %H:%M}  |  temperature={s.temperature} "
            f"seed={s.seed} top_p={s.top_p} max_tokens={s.max_tokens}\n"
            f"Saved: {path}\n"
            "Note: small samples; differences of a few points are often noise. "
            "See LIMITATIONS.md.",
            style="dim",
        )
    )
    if cfg.allow_unreviewed:
        console.print(
            Text(
                "UNREVIEWED DATA: these items were not checked by two reviewers. "
                "Do not publish these numbers.",
                style="bold yellow",
            )
        )


@app.command("list-tasks")
def list_tasks() -> None:
    """Show available tasks and how many reviewed items each has."""
    table = Table()
    table.add_column("Task")
    table.add_column("Version", justify="right")
    table.add_column("Items", justify="right")
    table.add_column("Description")
    for name in available_tasks():
        task = get_task(name)
        try:
            count = str(len(task.load_samples()))
        except DatasetError:
            count = "0"
        table.add_row(name, task.version, count, task.description)
    console.print(table)


@app.command("list-models")
def list_models(
    provider: str = typer.Argument(..., help=f"One of: {', '.join(available_backends())}."),
    env_file: Path | None = typer.Option(None, help="Path to a .env file with API keys."),
) -> None:
    """List model ids the provider offers right now (ids change; check before each run)."""
    load_env(env_file)
    try:
        backend = get_backend(provider)
        try:
            ids = backend.list_models()
        finally:
            backend.close()
    except KasautiError as err:
        raise _fail(str(err)) from None
    if not ids:
        console.print(f"{provider} returned no models.")
        return
    for model_id in ids:
        console.print(Text(f"{provider}/{model_id}"))
    console.print(Text(f"{len(ids)} model(s) as of {date.today().isoformat()}", style="dim"))


if __name__ == "__main__":
    app()
