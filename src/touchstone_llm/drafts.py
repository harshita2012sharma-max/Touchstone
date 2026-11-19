"""Where draft (not yet reviewed) questions live.

Drafts ship inside the package so a fresh ``pip install`` has something to try,
but they are never used unless the user asks for them (``--drafts`` on the CLI
or the "Use draft questions" box in the UI), and every result made with them
is marked as unreviewed.

- Installed wheel: ``touchstone_llm/tasks/data/drafts/`` (copied at build time).
- Source checkout: ``datasets/pending/`` at the repository root.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

_SOURCE_CHECKOUT = Path(__file__).resolve().parents[2] / "datasets" / "pending"


def default_drafts_dir() -> Path | None:
    """Return the folder with draft ``<task>.jsonl`` files, or ``None`` if there is none."""
    packaged = Path(str(files("touchstone_llm.tasks").joinpath("data").joinpath("drafts")))
    for candidate in (packaged, _SOURCE_CHECKOUT):
        if candidate.is_dir() and any(candidate.glob("*.jsonl")):
            return candidate
    return None
