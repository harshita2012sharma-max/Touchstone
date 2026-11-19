from pathlib import Path

from conftest import CountingMock, write_jsonl
from touchstone_llm.config import RunConfig
from touchstone_llm.reproduce import compare_runs
from touchstone_llm.runner import Runner


def _run(data_dir: Path):
    cfg = RunConfig(model="mock/echo", tasks=["hindi_reasoning"], data_dir=str(data_dir))
    return Runner(cfg, backend=CountingMock(), cache=None).run()


def test_identical_rerun_matches(data_dir: Path) -> None:
    report = compare_runs(_run(data_dir), _run(data_dir))
    assert report.prompts_identical
    assert report.settings_identical
    row = report.rows[0]
    assert (row.task, row.old_score, row.new_score) == (
        "hindi_reasoning",
        row.new_score,
        row.old_score,
    )
    assert row.changed_outputs == 0


def test_changed_data_is_flagged(data_dir: Path) -> None:
    old = _run(data_dir)
    write_jsonl(
        data_dir / "hindi_reasoning.jsonl",
        [
            {
                "id": "hindi_reasoning-001",
                "author": "w",
                "license": "CC-BY-4.0",
                "reviewers": ["a", "b"],
                "question": "changed?",
                "answer": 1,
            }
        ],
    )
    report = compare_runs(old, _run(data_dir))
    assert not report.prompts_identical
    assert report.rows[0].missing_samples == ["hindi_reasoning-002", "hindi_reasoning-003"]
