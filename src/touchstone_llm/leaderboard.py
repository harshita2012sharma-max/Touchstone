"""Turn saved runs into a leaderboard: a Markdown table, a JSON file and an SVG chart.

The leaderboard follows the same rules as every touchstone report:

- Only runs with identical settings and the same task versions are compared;
  the mean is taken over the tasks that every included run covers.
- The latest run of each model is used, and its date and the model id the
  provider reported are shown next to the score.
- Equal scores share a rank ("=") and sample sizes are always shown. Small
  differences are often noise; the output says so.
- If any run used draft (unreviewed) questions, every output is stamped as a
  practice leaderboard that must not be published.

The SVG chart is self-contained (no fonts or scripts to load) so it can be
posted as an image or embedded in a README.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from touchstone_llm.results import RunResult

TASK_LABELS = {
    "hindi_comprehension": "Hindi reading",
    "hinglish_understanding": "Hinglish chat",
    "translation_hi_en": "Hindi to English",
    "codemixed_instructions": "Hinglish instructions",
    "hindi_reasoning": "Hindi maths",
    "cultural_context": "Everyday India",
    "hindi_grammar": "Hindi grammar",
    "idioms_proverbs": "Idioms",
    "hindi_logic": "Hindi logic",
    "translation_en_hi": "English to Hindi",
    "hinglish_to_hindi": "Hinglish to Hindi",
}
PRACTICE_NOTE = "PRACTICE: draft questions not yet reviewed by two people. Do not publish."
NOISE_NOTE = (
    "Scores come from a small set of questions; differences of a few points are often noise."
)


class LeaderboardError(ValueError):
    """The given runs cannot be compared fairly."""


@dataclass
class Entry:
    """One model's row on the leaderboard."""

    model: str
    provider_model_id: str | None
    date: str
    run_id: str
    mean: float
    n: int
    scores: dict[str, float]
    rank: str = ""


@dataclass
class Leaderboard:
    """A ranked set of entries over a fixed list of tasks."""

    tasks: list[str]
    entries: list[Entry]
    practice: bool
    settings: dict[str, object]
    skipped: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        """Machine-readable copy of the leaderboard."""
        return json.dumps(
            {
                "practice": self.practice,
                "tasks": self.tasks,
                "settings": self.settings,
                "entries": [e.__dict__ for e in self.entries],
                "skipped": self.skipped,
            },
            indent=2,
            ensure_ascii=False,
        )

    def to_markdown(self) -> str:
        """Render the table for a README or a blog post."""
        lines = ["# touchstone leaderboard: Hindi and Hinglish", ""]
        if self.practice:
            lines += [f"> **{PRACTICE_NOTE}**", ""]
        labels = [TASK_LABELS.get(t, t) for t in self.tasks]
        header = ["Rank", "Model", "Mean", *labels, "n", "Date"]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")
        for e in self.entries:
            model = f"{e.model} (`{e.provider_model_id}`)" if e.provider_model_id else e.model
            task_cells = [_pct(e.scores[t]) for t in self.tasks]
            cells = [e.rank, model, _pct(e.mean), *task_cells, str(e.n), e.date]
            lines.append("| " + " | ".join(cells) + " |")
        settings = ", ".join(f"{k} {v}" for k, v in self.settings.items())
        lines += [
            "",
            "Mean = average of the task scores (each task counts equally). "
            "n = questions per model. "
            f"Same prompts and settings for every model ({settings}).",
            "",
            NOISE_NOTE,
        ]
        if self.skipped:
            lines += ["", "Not included: " + "; ".join(self.skipped)]
        return "\n".join(lines) + "\n"

    def to_svg(self, title: str = "Which AI understands Hindi and Hinglish best?") -> str:
        """Draw a shareable horizontal bar chart in the deep teal brand colours."""
        width, left, right, top, bar_h, gap = 1000, 420, 90, 150, 34, 14
        rows = self.entries
        height = top + len(rows) * (bar_h + gap) + 90
        span = width - left - right
        muted, ink, maroon = "#3f5a5e", "#0e2931", "#12484c"
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
            "<defs><linearGradient id='g' x1='0' x2='1'>"
            "<stop offset='0' stop-color='#0e2931'/><stop offset='1' stop-color='#287574'/>"
            "</linearGradient><linearGradient id='rule' x1='0' x2='1'>"
            "<stop offset='0' stop-color='#0e2931'/><stop offset='0.5' stop-color='#287574'/>"
            "<stop offset='1' stop-color='#861211'/>"
            "</linearGradient></defs>",
            f'<rect width="{width}" height="{height}" fill="#f7f7f5"/>',
            f'<rect width="{width}" height="6" fill="url(#rule)"/>',
            '<g font-family="Segoe UI, Helvetica, Arial, sans-serif">',
            _text(40, 62, 30, ink, title, bold=True),
            _text(
                40,
                96,
                17,
                muted,
                f"Mean score over {len(self.tasks)} tasks · same prompts and settings "
                "for every model · touchstone",
            ),
        ]
        if self.practice:
            out.append(_text(40, 124, 15, "#b42318", PRACTICE_NOTE, bold=True))
        for i, e in enumerate(rows):
            y = top + i * (bar_h + gap)
            base = y + bar_h * 0.68
            w = max(2.0, e.mean * span)
            label = e.model if len(e.model) <= 38 else e.model[:37] + "…"
            out += [
                _text(40, base, 17, muted, e.rank),
                _text(80, base, 17, ink, label, bold=True),
                f'<rect x="{left}" y="{y}" width="{span}" height="{bar_h}" rx="8" fill="#e2e2e0"/>',
                f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="8" '
                'fill="url(#g)"/>',
                _text(left + w + 10, base, 17, maroon, _pct(e.mean), bold=True),
            ]
        foot = height - 40
        n_text = ", ".join(sorted({str(e.n) for e in rows}))
        out += [
            _text(40, foot, 14, muted, f"n = {n_text} questions per model. {NOISE_NOTE}"),
            _text(40, foot + 22, 14, muted, "github.com/harshita2012sharma-max/Touchstone"),
            "</g></svg>",
        ]
        return "\n".join(out) + "\n"


def _text(x: float, y: float, size: int, fill: str, content: str, *, bold: bool = False) -> str:
    weight = ' font-weight="700"' if bold else ""
    return (
        f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}"{weight} fill="{fill}">'
        f"{escape(content)}</text>"
    )


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def build(results: list[RunResult], *, include_mock: bool = False) -> Leaderboard:
    """Rank the latest run of each model over the tasks every run covers."""
    skipped: list[str] = []
    latest: dict[str, RunResult] = {}
    for r in results:
        model = r.config.model
        if model.startswith("mock/") and not include_mock:
            continue
        old = latest.get(model)
        if old is None or r.metadata.started_at > old.metadata.started_at:
            latest[model] = r
    if not latest:
        raise LeaderboardError("No runs to rank (practice-model runs are left out by default).")

    runs = sorted(latest.values(), key=lambda r: r.metadata.started_at, reverse=True)
    reference = runs[0].config.settings
    kept = []
    for r in runs:
        if r.config.settings != reference:
            skipped.append(f"{r.config.model} (different settings)")
        else:
            kept.append(r)

    versions: dict[str, set[str]] = {}
    for r in kept:
        for t in r.tasks:
            versions.setdefault(t.task, set()).add(t.task_version)
    common = [
        t
        for t in versions
        if len(versions[t]) == 1 and all(any(x.task == t for x in r.tasks) for r in kept)
    ]
    if not common:
        raise LeaderboardError(
            "The runs share no task with the same version, so they cannot be compared. "
            "Run every model on the same tasks."
        )
    order = list(TASK_LABELS)
    common.sort(key=lambda t: (order.index(t) if t in order else len(order), t))

    entries = []
    for r in kept:
        by_task = {t.task: t for t in r.tasks}
        scores = {t: by_task[t].score for t in common}
        entries.append(
            Entry(
                model=r.config.model,
                provider_model_id=r.metadata.provider_model_id,
                date=r.metadata.started_at.date().isoformat(),
                run_id=r.metadata.run_id,
                mean=sum(scores.values()) / len(scores),
                n=sum(by_task[t].n for t in common),
                scores=scores,
            )
        )
    entries.sort(key=lambda e: (-round(e.mean, 6), e.model))
    for i, e in enumerate(entries):
        same_as_prev = i > 0 and round(e.mean, 6) == round(entries[i - 1].mean, 6)
        e.rank = f"={entries[i - 1].rank.lstrip('=')}" if same_as_prev else str(i + 1)
        if same_as_prev and not entries[i - 1].rank.startswith("="):
            entries[i - 1].rank = "=" + entries[i - 1].rank

    return Leaderboard(
        tasks=common,
        entries=entries,
        practice=any(r.config.allow_unreviewed for r in kept),
        settings={k: v for k, v in reference.model_dump().items() if k != "max_tokens"},
        skipped=skipped,
    )


def write(board: Leaderboard, out_dir: Path) -> list[Path]:
    """Save leaderboard.md, leaderboard.json and leaderboard.svg into ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, text in (
        ("leaderboard.md", board.to_markdown()),
        ("leaderboard.json", board.to_json()),
        ("leaderboard.svg", board.to_svg()),
    ):
        path = out_dir / name
        path.write_text(text, encoding="utf-8")
        paths.append(path)
    return paths
