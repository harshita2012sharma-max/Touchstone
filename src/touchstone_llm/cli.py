"""Command-line interface: ``touchstone run``, ``list-tasks``, ``list-models``."""

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

from touchstone_llm import __version__
from touchstone_llm.backends import available_backends, get_backend
from touchstone_llm.cache import ResponseCache
from touchstone_llm.config import GenerationSettings, RunConfig
from touchstone_llm.drafts import default_drafts_dir
from touchstone_llm.env import load_env, redact_secrets
from touchstone_llm.errors import TouchstoneError
from touchstone_llm.report import write_reports
from touchstone_llm.reproduce import compare_runs
from touchstone_llm.results import RunResult
from touchstone_llm.runner import ProgressEvent, Runner
from touchstone_llm.tasks import available_tasks, get_task
from touchstone_llm.tasks.base import DatasetError

app = typer.Typer(
    name="touchstone",
    help="A touchstone for LLMs in Hindi and Hinglish.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console(highlight=False)


def _fail(message: str) -> typer.Exit:
    """Print a clean, redacted error (no traceback) and return an exit to raise."""
    console.print(Text(f"Error: {redact_secrets(message)}", style="bold red"), soft_wrap=True)
    return typer.Exit(code=1)


def _validation_message(err: ValidationError) -> str:
    return "; ".join(str(e["msg"]).removeprefix("Value error, ") for e in err.errors())


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"touchstone {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the installed touchstone version and exit.",
        callback=_print_version,
        is_eager=True,
    ),
) -> None:
    """Run small, reproducible LLM evals in Hindi and Hinglish."""


@app.command()
def run(
    model: str = typer.Option(
        ..., "--model", "-m", help="provider/model-id. See `touchstone list-models <provider>`."
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
    drafts: bool = typer.Option(
        False,
        "--drafts",
        help="Use the draft questions that ship with touchstone (marked unreviewed).",
    ),
    no_cache: bool = typer.Option(False, "--no-cache", help="Ignore cached replies."),
    env_file: Path | None = typer.Option(None, help="Path to a .env file with API keys."),
) -> None:
    """Run tasks against a model and print a score table.

    Temperature (0) and seed (42) are fixed so every model is tested the same way.
    """
    load_env(env_file)
    names = available_tasks() if tasks.strip().lower() == "all" else tasks.split(",")
    if drafts:
        found = default_drafts_dir()
        if found is None:
            raise _fail("No draft questions were found in this installation.")
        data_dir, allow_unreviewed = found, True
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

    result = _execute(config, rpm=rpm, use_cache=not no_cache)
    paths = _save_all(result, output_dir)
    _print_summary(result, paths)


def _execute(config: RunConfig, *, rpm: float | None, use_cache: bool) -> RunResult:
    """Run with a progress bar; turn expected errors into clean CLI failures."""
    try:
        overrides = {"requests_per_minute": rpm} if rpm else {}
        backend = get_backend(config.model_ref.provider, **overrides)
        cache = ResponseCache() if use_cache else None
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
                return Runner(config, backend=backend, cache=cache, on_event=on_event).run()
            finally:
                backend.close()
    except TouchstoneError as err:
        raise _fail(str(err)) from None
    except KeyboardInterrupt:
        raise _fail("Stopped by user. Cached replies are kept; run again to resume.") from None


def _save_all(result: RunResult, output_dir: Path) -> list[Path]:
    """Save the JSON result plus Markdown and HTML reports."""
    json_path = result.save(output_dir)
    md_path, html_path = write_reports(result, output_dir)
    return [json_path, md_path, html_path]


def _load_result(path: Path) -> RunResult:
    try:
        return RunResult.load(path)
    except FileNotFoundError:
        raise _fail(f"File not found: {path}") from None
    except ValidationError as err:
        raise _fail(
            f"{path} is not a touchstone result file: {err.error_count()} error(s)"
        ) from None


def _print_summary(result: RunResult, paths: list[Path]) -> None:
    meta, cfg = result.metadata, result.config
    table = Table(title=f"touchstone results: {cfg.model}", title_justify="left")
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
            "Saved: " + ", ".join(str(p) for p in paths) + "\n"
            "Note: small samples; differences of a few points are often noise. "
            "See LIMITATIONS.md.",
            style="dim",
        ),
        soft_wrap=True,  # keep file paths on one line so they can be copied
    )
    if cfg.allow_unreviewed:
        console.print(
            Text(
                "UNREVIEWED DATA: these items were not checked by two reviewers. "
                "Do not publish these numbers.",
                style="bold yellow",
            )
        )


@app.command()
def report(
    result_file: Path = typer.Argument(..., help="A result JSON saved by `touchstone run`."),
    out_dir: Path | None = typer.Option(None, help="Folder for the reports (default: same)."),
) -> None:
    """Rebuild the HTML and Markdown reports from a saved result."""
    result = _load_result(result_file)
    md_path, html_path = write_reports(result, out_dir or result_file.parent)
    console.print(Text(f"Wrote {md_path} and {html_path}"))


@app.command()
def reproduce(
    result_file: Path = typer.Argument(..., help="A result JSON saved by `touchstone run`."),
    output_dir: Path = typer.Option(Path("runs"), help="Where to save the new result."),
    use_cache: bool = typer.Option(
        False, "--use-cache", help="Reuse cached replies (checks prompts only, not the model)."
    ),
    env_file: Path | None = typer.Option(None, help="Path to a .env file with API keys."),
) -> None:
    """Rerun a saved result with the exact same config and compare."""
    load_env(env_file)
    old = _load_result(result_file)
    new = _execute(old.config, rpm=None, use_cache=use_cache)
    paths = _save_all(new, output_dir)
    cmp = compare_runs(old, new)

    table = Table(title="Reproduction check", title_justify="left")
    table.add_column("Task")
    table.add_column("Old score", justify="right")
    table.add_column("New score", justify="right")
    table.add_column("Changed outputs", justify="right")
    for row in cmp.rows:
        table.add_row(
            row.task,
            "-" if row.old_score is None else f"{row.old_score:.1%}",
            "-" if row.new_score is None else f"{row.new_score:.1%}",
            str(row.changed_outputs),
        )
    console.print(table)
    console.print(Text(f"Prompts identical: {'yes' if cmp.prompts_identical else 'NO'}"))
    console.print(Text(f"Settings identical: {'yes' if cmp.settings_identical else 'NO'}"))
    if old.metadata.tool_version != new.metadata.tool_version:
        console.print(
            Text(
                f"touchstone version changed: {old.metadata.tool_version} -> "
                f"{new.metadata.tool_version}",
                style="yellow",
            )
        )
    console.print(Text("Saved: " + ", ".join(str(p) for p in paths), style="dim"))


@app.command()
def ui(
    port: int = typer.Option(7860, min=1024, max=65535, help="Port on 127.0.0.1."),
    runs_dir: Path = typer.Option(Path("runs"), help="Folder with saved runs."),
    drafts_dir: Path | None = typer.Option(
        None, help="Draft questions folder (default: the drafts that ship with touchstone)."
    ),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open a browser tab."),
    env_file: Path | None = typer.Option(None, help="Path to a .env file with API keys."),
) -> None:
    """Start the local web UI (only reachable from this computer)."""
    try:
        import uvicorn

        from touchstone_llm.server.app import create_app
    except ImportError:
        raise _fail('The web UI needs extra packages: pip install "touchstone-llm[ui]"') from None
    load_env(env_file)
    runs_dir.mkdir(parents=True, exist_ok=True)
    drafts = drafts_dir if drafts_dir and drafts_dir.is_dir() else default_drafts_dir()
    app_ = create_app(runs_dir=runs_dir, drafts_dir=drafts)
    url = f"http://127.0.0.1:{port}"
    console.print(Text(f"touchstone UI running at {url}  (Ctrl+C to stop)"))
    if open_browser:
        import webbrowser

        webbrowser.open(url)
    uvicorn.run(app_, host="127.0.0.1", port=port, log_level="warning")


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
    except TouchstoneError as err:
        raise _fail(str(err)) from None
    if not ids:
        console.print(f"{provider} returned no models.")
        return
    for model_id in ids:
        console.print(Text(f"{provider}/{model_id}"))
    console.print(Text(f"{len(ids)} model(s) as of {date.today().isoformat()}", style="dim"))


if __name__ == "__main__":
    app()
