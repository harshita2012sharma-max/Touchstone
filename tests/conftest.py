import json
from pathlib import Path
from typing import Any

import pytest

from touchstone_llm.backends.base import Backend, Completion
from touchstone_llm.backends.mock import MockBackend
from touchstone_llm.config import GenerationSettings

META = {"author": "writer", "license": "CC-BY-4.0", "reviewers": ["rev1", "rev2"]}


def write_jsonl(path: Path, items: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), "utf-8")
    return path


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Tiny reviewed dataset for two tasks."""
    d = tmp_path / "data"
    write_jsonl(
        d / "hindi_reasoning.jsonl",
        [
            {"id": f"hindi_reasoning-00{i}", **META, "question": f"{i} + {i} = ?", "answer": 2 * i}
            for i in (1, 2, 3)
        ],
    )
    write_jsonl(
        d / "cultural_context.jsonl",
        [
            {
                "id": "cultural_context-001",
                **META,
                "question": "भारत का राष्ट्रीय पशु?",
                "options": ["शेर", "बाघ"],
                "answer": "B",
            }
        ],
    )
    return d


class CountingMock(MockBackend):
    """Mock that counts real (non-cached) calls and can fail on demand."""

    def __init__(self, replies: dict[str, str] | None = None, fail: Exception | None = None):
        super().__init__(replies=replies)
        self.calls = 0
        self.fail = fail

    def _generate(self, model_id: str, prompt: str, settings: GenerationSettings) -> Completion:
        self.calls += 1
        if self.fail is not None:
            raise self.fail
        return super()._generate(model_id, prompt, settings)


@pytest.fixture
def counting_mock() -> type[Backend]:
    return CountingMock
