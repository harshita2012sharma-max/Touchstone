import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from touchstone_llm import __version__
from touchstone_llm.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)  # cache and runs/ go into the temp folder
    for name in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_version_flag_prints_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"touchstone {__version__}"


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    assert "Usage" in result.output


def test_run_with_mock_saves_result(data_dir: Path, tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            "--model",
            "mock/fixed",
            "--tasks",
            "hindi_reasoning,cultural_context",
            "--data-dir",
            str(data_dir),
            "--output-dir",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "hindi_reasoning" in result.output
    assert "cultural_context" in result.output
    saved = list((tmp_path / "out").glob("*.json"))
    assert len(saved) == 1
    data = json.loads(saved[0].read_text("utf-8"))
    assert data["config"]["model"] == "mock/fixed"
    assert data["config"]["settings"]["temperature"] == 0.0


def test_run_all_tasks_keyword(data_dir: Path) -> None:
    result = runner.invoke(
        app, ["run", "--model", "mock/fixed", "--tasks", "all", "--data-dir", str(data_dir)]
    )
    # data_dir has only two of the six tasks, so this must fail clearly
    assert result.exit_code == 1
    assert "No data found" in result.output


def test_missing_key_is_friendly_not_traceback() -> None:
    result = runner.invoke(app, ["run", "--model", "groq/some-model", "--tasks", "hindi_reasoning"])
    assert result.exit_code == 1
    assert "GROQ_API_KEY" in result.output
    assert "Traceback" not in result.output


def test_bad_model_string() -> None:
    result = runner.invoke(app, ["run", "--model", "nomodel", "--tasks", "hindi_reasoning"])
    assert result.exit_code == 1
    assert "provider/model" in result.output


def test_unreviewed_run_warns(tmp_path: Path) -> None:
    pending = tmp_path / "pending"
    pending.mkdir()
    (pending / "hindi_reasoning.jsonl").write_text(
        json.dumps(
            {
                "id": "hindi_reasoning-001",
                "author": "w",
                "license": "CC-BY-4.0",
                "reviewers": [],
                "question": "1+1?",
                "answer": 2,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        [
            "run",
            "--model",
            "mock/fixed",
            "--tasks",
            "hindi_reasoning",
            "--data-dir",
            str(pending),
            "--allow-unreviewed",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "UNREVIEWED" in result.output


def test_list_tasks() -> None:
    result = runner.invoke(app, ["list-tasks"])
    assert result.exit_code == 0
    assert "hinglish_understanding" in result.output


def test_list_models_mock() -> None:
    result = runner.invoke(app, ["list-models", "mock"])
    assert result.exit_code == 0
    assert "echo" in result.output
    assert "fixed" in result.output


def _mock_run(data_dir: Path, out: Path) -> Path:
    result = runner.invoke(
        app,
        [
            "run",
            "--model",
            "mock/fixed",
            "--tasks",
            "hindi_reasoning",
            "--data-dir",
            str(data_dir),
            "--output-dir",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    return next(out.glob("*.json"))


def test_run_writes_html_and_markdown(data_dir: Path, tmp_path: Path) -> None:
    saved = _mock_run(data_dir, tmp_path / "out")
    assert saved.with_suffix(".html").is_file()
    assert saved.with_suffix(".md").is_file()


def test_report_command_rebuilds(data_dir: Path, tmp_path: Path) -> None:
    saved = _mock_run(data_dir, tmp_path / "out")
    result = runner.invoke(app, ["report", str(saved), "--out-dir", str(tmp_path / "r")])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "r" / saved.with_suffix(".html").name).is_file()


def test_reproduce_command(data_dir: Path, tmp_path: Path) -> None:
    saved = _mock_run(data_dir, tmp_path / "out")
    result = runner.invoke(app, ["reproduce", str(saved), "--output-dir", str(tmp_path / "re")])
    assert result.exit_code == 0, result.output
    assert "Prompts identical: yes" in result.output
    assert "Settings identical: yes" in result.output


def test_report_on_bad_file(tmp_path: Path) -> None:
    bad = tmp_path / "x.json"
    bad.write_text("{}", encoding="utf-8")
    result = runner.invoke(app, ["report", str(bad)])
    assert result.exit_code == 1
    assert "not a touchstone result" in result.output
