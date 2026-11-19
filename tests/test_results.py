from pathlib import Path

import pytest

from touchstone_llm.config import RunConfig
from touchstone_llm.results import RunMetadata, RunResult, SampleResult, TaskResult


def _sample(sid: str, score: float, unparsed: bool = False) -> SampleResult:
    return SampleResult(
        sample_id=sid,
        prompt="प्रश्न?",
        output="B",
        expected="B",
        score=score,
        unparsed=unparsed,
    )


def test_task_result_aggregates() -> None:
    task = TaskResult.from_samples(
        "hindi_comprehension",
        task_version="1",
        prompt_template="T: {question}",
        samples=[
            _sample("1", 1.0),
            _sample("2", 0.0, unparsed=True),
            _sample("3", 1.0),
            _sample("4", 0.0),
        ],
    )
    assert task.n == 4
    assert task.score == pytest.approx(0.5)
    assert task.unparsed_rate == pytest.approx(0.25)
    assert task.errors == 0


def test_task_result_empty_is_zero_not_crash() -> None:
    task = TaskResult.from_samples("t", task_version="1", prompt_template="", samples=[])
    assert task.n == 0
    assert task.score == 0.0
    assert task.unparsed_rate == 0.0


def test_sample_score_must_be_between_0_and_1() -> None:
    with pytest.raises(ValueError):
        _sample("x", 1.5)


def test_run_result_round_trip_keeps_hindi(tmp_path: Path) -> None:
    config = RunConfig(model="mock/fake", tasks=["hindi_comprehension"])
    task = TaskResult.from_samples(
        "hindi_comprehension", task_version="1", prompt_template="T", samples=[_sample("1", 1.0)]
    )
    run = RunResult(metadata=RunMetadata.new(config), config=config, tasks=[task])
    path = run.save(tmp_path)
    assert path.parent == tmp_path
    assert path.suffix == ".json"
    raw = path.read_text(encoding="utf-8")
    assert "प्रश्न" in raw  # stored as readable UTF-8, not \u escapes
    loaded = RunResult.load(path)
    assert loaded == run
    assert loaded.metadata.schema_version == 1


def test_metadata_records_reproducibility_fields() -> None:
    config = RunConfig(model="mock/fake", tasks=["t"])
    meta = RunMetadata.new(config)
    assert meta.tool_version
    assert meta.python_version
    assert meta.platform
    assert meta.started_at.tzinfo is not None
    assert meta.run_id.startswith(meta.started_at.strftime("%Y%m%d"))


def test_saved_result_never_contains_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "gsk_should_never_be_saved_123"
    monkeypatch.setenv("GROQ_API_KEY", secret)
    config = RunConfig(model="groq/fake", tasks=["t"])
    run = RunResult(metadata=RunMetadata.new(config), config=config, tasks=[])
    path = run.save(tmp_path)
    assert secret not in path.read_text(encoding="utf-8")
