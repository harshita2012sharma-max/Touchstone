"""On-disk cache of model replies (SQLite, standard library only).

Free tiers have daily limits and laptops crash. Every reply is stored as
soon as it arrives, keyed by model, exact prompt and settings, so running
the same command again resumes where it stopped instead of paying twice.
The cache stores prompts and replies only, never API keys.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from touchstone_llm.backends.base import Completion
from touchstone_llm.config import GenerationSettings

DEFAULT_CACHE_PATH = Path(".touchstone") / "cache.sqlite"


def cache_key(model: str, prompt: str, settings: GenerationSettings) -> str:
    """Stable hash of everything that determines a reply."""
    payload = json.dumps(
        {"model": model, "prompt": prompt, "settings": settings.model_dump()},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ResponseCache:
    """Key-value store of :class:`Completion` objects in one SQLite file."""

    def __init__(self, path: str | Path = DEFAULT_CACHE_PATH) -> None:
        """Create the file and table if needed."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS responses ("
                "key TEXT PRIMARY KEY, completion TEXT NOT NULL, "
                "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )

    def get(self, key: str) -> Completion | None:
        """Return the cached reply, or ``None``."""
        with closing(sqlite3.connect(self.path)) as conn:
            row = conn.execute("SELECT completion FROM responses WHERE key = ?", (key,)).fetchone()
        return Completion.model_validate_json(row[0]) if row else None

    def put(self, key: str, completion: Completion) -> None:
        """Store (or replace) a reply."""
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute(
                "INSERT OR REPLACE INTO responses (key, completion) VALUES (?, ?)",
                (key, completion.model_dump_json()),
            )
