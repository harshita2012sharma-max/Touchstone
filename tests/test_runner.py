from pathlib import Path

import pytest

from conftest import CountingMock, write_jsonl
from touchstone_llm.backends.base import AuthError, TransientError
from touchstone_llm.cache import ResponseCache
from touchstone_llm.config import RunConfig
from touchstone_llm.errors import TouchstoneError
from touchstone_llm.runner import ProgressEvent, Runner, RunStopped


def _config(data_dir: Path, **kw: object) -> RunConfig:
    return RunConfig(
        model="mock/echo",
        tasks=["hindi_reasoning", "cultural_context"],
        data_dir=str(data_dir),
        **kw,
    )


def _replies(data_dir: Path) -> dict[str, str]:
    from touchstone_llm.tasks import get_task

    task = get_task("hindi_reasoning", data_path=data_dir / "hindi_reasoning.jsonl")
    replies = {}
    for s in task.load_samples():
        replies[task.build_prompt(s)] = "Answer: 2" if s.id.endswith("1") else "Answer: 99"
    return replies


def test_run_scores_and_records_everything(data_dir: Path, tmp_path: Path) -> None:
    backend = CountingMock(replies=_replies(data_dir))
    events: list[ProgressEvent] = []
    result = Runner(
        _config(data_dir),
        backend=backend,
        cache=ResponseCache(tmp_path / "c.sqlite"),
        on_event=events.append,
    ).run()

    reasoning, cultural = result.tasks
    assert reasoning.task == "hindi_reasoning"
    assert reasoning.n == 3
    assert reasoning.score == pytest.approx(1 / 3)
    assert reasoning.prompt_template.startswith("{question}")
    first = reasoning.samples[0]
    assert first.prompt.startswith("1 + 1 = ?")
    assert first.output == "Answer: 2"
    assert first.expected == "2"
    assert first.parsed == "2"
    assert cultural.n == 1
    assert result.metadata.provider_model_id == "mock-echo"
    assert result.metadata.finished_at is not None
    assert backend.calls == 4
    kinds = [e.kind for e in events]
    assert kinds[0] == "task_start"
    assert kinds.count("sample_done") == 4
    assert kinds[-1] == "task_done"


def test_limit_applies_per_task(data_dir: Path, tmp_path: Path) -> None:
    result = Runner(
        _config(data_dir, limit=2), backend=CountingMock(), cache=ResponseCache(tmp_path / "c")
    ).run()
    assert [t.n for t in result.tasks] == [2, 1]


def test_second_run_uses_cache(data_dir: Path, tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "c.sqlite")
    first = CountingMock()
    Runner(_config(data_dir), backend=first, cache=cache).run()
    second = CountingMock()
    events: list[ProgressEvent] = []
    Runner(_config(data_dir), backend=second, cache=cache, on_event=events.append).run()
    assert second.calls == 0
    assert all(e.cached for e in events if e.kind == "sample_done")


def test_without_cache_always_calls(data_dir: Path) -> None:
    backend = CountingMock()
    Runner(_config(data_dir), backend=backend, cache=None).run()
    Runner(_config(data_dir), backend=backend, cache=None).run()
    assert backend.calls == 8


@pytest.mark.parametrize("error", [AuthError("bad key"), TransientError("503 again")])
def test_failures_stop_run_with_resume_hint(
    data_dir: Path, tmp_path: Path, error: Exception
) -> None:
    backend = CountingMock(fail=error)
    with pytest.raises(RunStopped) as exc:
        Runner(_config(data_dir), backend=backend, cache=ResponseCache(tmp_path / "c")).run()
    msg = str(exc.value)
    assert str(error) in msg
    assert "run the same command again" in msg
    assert isinstance(exc.value, TouchstoneError)


def test_unreviewed_data_needs_flag(tmp_path: Path) -> None:
    write_jsonl(
        tmp_path / "hindi_reasoning.jsonl",
        [
            {
                "id": "hindi_reasoning-001",
                "author": "w",
                "license": "CC-BY-4.0",
                "reviewers": [],
                "question": "1+1?",
                "answer": 2,
            }
        ],
    )
    cfg = RunConfig(model="mock/echo", tasks=["hindi_reasoning"], data_dir=str(tmp_path))
    with pytest.raises(TouchstoneError, match="reviewers"):
        Runner(cfg, backend=CountingMock(), cache=None).run()
    cfg = cfg.model_copy(update={"allow_unreviewed": True})
    result = Runner(cfg, backend=CountingMock(), cache=None).run()
    assert result.tasks[0].n == 1
    assert result.config.allow_unreviewed is True


def test_missing_task_file_in_data_dir(tmp_path: Path) -> None:
    cfg = RunConfig(model="mock/echo", tasks=["hindi_reasoning"], data_dir=str(tmp_path))
    with pytest.raises(TouchstoneError, match="No data"):
        Runner(cfg, backend=CountingMock(), cache=None).run()


def test_provider_notes_are_recorded(data_dir: Path) -> None:
    from touchstone_llm.backends.base import Completion

    class NotingMock(CountingMock):
        def _generate(self, model_id, prompt, settings):  # type: ignore[no-untyped-def]
            out = super()._generate(model_id, prompt, settings)
            return out.model_copy(update={"notes": ["mock rejected 'seed', so it was not sent"]})

    result = Runner(_config(data_dir), backend=NotingMock(), cache=None).run()
    assert result.metadata.provider_notes == ["mock rejected 'seed', so it was not sent"]
    assert isinstance(Completion(text="x").notes, list)
