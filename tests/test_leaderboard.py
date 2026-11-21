from datetime import timedelta
from pathlib import Path

import pytest

from conftest import CountingMock
from touchstone_llm.config import GenerationSettings, RunConfig
from touchstone_llm.leaderboard import LeaderboardError, build, write
from touchstone_llm.results import RunResult
from touchstone_llm.runner import Runner

TASKS = ["hindi_reasoning", "cultural_context"]


def _run(data_dir: Path, model: str) -> RunResult:
    cfg = RunConfig(model="mock/fixed", tasks=TASKS, data_dir=str(data_dir))
    result = Runner(cfg, backend=CountingMock(), cache=None).run()
    result.config = result.config.model_copy(update={"model": model})
    return result


def test_ranks_latest_run_per_model_and_shares_ties(data_dir: Path) -> None:
    a = _run(data_dir, "groq/a")
    b = _run(data_dir, "groq/b")  # same replies as a, so a tie
    c = _run(data_dir, "groq/c")
    c.tasks[0].score = 1.0  # c did better on one task
    old_c = _run(data_dir, "groq/c")
    old_c.metadata.started_at -= timedelta(days=30)

    board = build([a, b, c, old_c])

    assert [e.model for e in board.entries] == ["groq/c", "groq/a", "groq/b"]
    assert [e.rank for e in board.entries] == ["1", "=2", "=2"]
    assert board.tasks == ["hindi_reasoning", "cultural_context"]
    assert board.entries[0].n == 4
    assert board.practice is False


def test_practice_mock_left_out_unless_asked(data_dir: Path) -> None:
    mock = _run(data_dir, "mock/fixed")
    with pytest.raises(LeaderboardError):
        build([mock])
    assert build([mock], include_mock=True).entries[0].model == "mock/fixed"


def test_different_settings_are_not_compared(data_dir: Path) -> None:
    a = _run(data_dir, "groq/a")
    b = _run(data_dir, "groq/b")
    b.config = b.config.model_copy(update={"settings": GenerationSettings(max_tokens=64)})
    b.metadata.started_at -= timedelta(days=1)
    board = build([a, b])
    assert [e.model for e in board.entries] == ["groq/a"]
    assert board.skipped == ["groq/b (different settings)"]


def test_outputs_are_written_and_marked_practice(data_dir: Path, tmp_path: Path) -> None:
    a = _run(data_dir, "groq/a")
    a.config = a.config.model_copy(update={"allow_unreviewed": True})
    board = build([a])
    paths = write(board, tmp_path / "lb")
    assert sorted(p.name for p in paths) == [
        "leaderboard.json",
        "leaderboard.md",
        "leaderboard.svg",
    ]
    md = (tmp_path / "lb" / "leaderboard.md").read_text(encoding="utf-8")
    svg = (tmp_path / "lb" / "leaderboard.svg").read_text(encoding="utf-8")
    assert "Do not publish" in md and "Do not publish" in svg
    assert "groq/a" in svg and svg.startswith("<svg")
