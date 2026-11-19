"""Static reports: a self-contained HTML page and a Markdown summary.

HTML is rendered with autoescaping, so model outputs (which may contain
HTML or script tags) are always shown as text. The page loads nothing from
the internet: no fonts, scripts or trackers.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from touchstone_llm import __version__
from touchstone_llm.results import RunResult

LIMITATIONS = [
    "Small dataset: a few points of difference between models is often noise.",
    "Hindi does not represent all of India; other languages and dialects are not covered.",
    "Hinglish has no standard spelling, so rule-based scoring can miss valid answers.",
    "Translation uses chrF against one or two references and can penalise good paraphrases.",
    "API models can change behind the same name; check the date and reported model id.",
    "Answers that cannot be parsed count as wrong; see the Unparsed column.",
]


def _pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def _md_cell(value: object) -> str:
    """Make text safe inside a Markdown table cell."""
    text = str(value).replace("\r", " ").replace("\n", " ")
    return text.replace("|", "\\|").strip()


def _env() -> Environment:
    env = Environment(
        loader=PackageLoader("touchstone_llm.report", "templates"),
        autoescape=select_autoescape(
            enabled_extensions=("html", "html.j2"), default_for_string=False
        ),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["pct"] = _pct
    env.filters["md"] = _md_cell
    return env


def _context(result: RunResult) -> dict[str, object]:
    total_n = sum(t.n for t in result.tasks)
    return {
        "r": result,
        "meta": result.metadata,
        "cfg": result.config,
        "s": result.config.settings,
        "total_n": total_n,
        "version": __version__,
        "limitations": LIMITATIONS,
    }


def render_html(result: RunResult) -> str:
    """Return the full HTML report as a string."""
    return _env().get_template("report.html.j2").render(**_context(result))


def render_markdown(result: RunResult) -> str:
    """Return the Markdown summary as a string."""
    return _env().get_template("report.md.j2").render(**_context(result))


def write_reports(result: RunResult, directory: str | Path) -> tuple[Path, Path]:
    """Write ``<run_id>.md`` and ``<run_id>.html`` into ``directory``."""
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / f"{result.metadata.run_id}.md"
    html_path = out / f"{result.metadata.run_id}.html"
    md_path.write_text(render_markdown(result), encoding="utf-8", newline="\n")
    html_path.write_text(render_html(result), encoding="utf-8", newline="\n")
    return md_path, html_path
