"""Command-line entry point for kasauti.

Only ``--version`` exists for now. Commands such as ``run`` and
``list-models`` are added in later build steps.
"""

from __future__ import annotations

import typer

from kasauti import __version__

app = typer.Typer(
    name="kasauti",
    help="A touchstone for LLMs in Hindi and Hinglish.",
    no_args_is_help=True,
    add_completion=False,
)


def _print_version(value: bool) -> None:
    """Print the installed version and exit when ``--version`` is passed."""
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


if __name__ == "__main__":
    app()
