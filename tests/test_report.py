from pathlib import Path

import pytest

from conftest import CountingMock
from kasauti.config import RunConfig
from kasauti.report import render_html, render_markdown, write_reports
from kasauti.results import RunResult
from kasauti.runner import Runner

EVIL = '<script>alert("x")</script> | pipe'


@pytest.fixture
def result(data_dir: Path) -> RunResult:
    cfg = RunConfig(
        model="mock/echo", tasks=["hindi_reasoning", "cultural_context"], data_dir=str(data_dir)
    )
    run = Runner(cfg, backend=CountingMock(), cache=None).run()
    # pretend the model replied with HTML/markdown-breaking text
    sample = run.tasks[0].samples[0].model_copy(update={"output": EVIL})
    run.tasks[0].samples[0] = sample
    return run


def test_html_escapes_model_output(result: RunResult) -> None:
    html = render_html(result)
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html


def test_html_has_metadata_and_settings(result: RunResult) -> None:
    html = render_html(result)
    for text in ("mock/echo", "mock-echo", "temperature", "seed", "42", "hindi_reasoning"):
        assert text in html
    assert "1 + 1 = ?" in html  # exact prompts are included
    assert "Limitations" in html
    assert "UNREVIEWED" not in html


def test_html_is_self_contained(result: RunResult) -> None:
    html = render_html(result)
    assert "http://" not in html.replace("http://www.w3.org", "")
    assert "<link" not in html
    assert 'src="http' not in html


def test_unreviewed_banner(result: RunResult) -> None:
    flagged = result.model_copy(
        update={"config": result.config.model_copy(update={"allow_unreviewed": True})}
    )
    assert "UNREVIEWED" in render_html(flagged)
    assert "UNREVIEWED" in render_markdown(flagged)


def test_markdown_summary_table(result: RunResult) -> None:
    md = render_markdown(result)
    assert "| Task | n | Score | Unparsed |" in md
    assert "| hindi_reasoning | 3 |" in md
    assert "temperature=0.0" in md
    assert "{question}" in md  # prompt template shown
    assert EVIL not in md  # pipes in outputs must not break tables


def test_write_reports_next_to_json(result: RunResult, tmp_path: Path) -> None:
    md_path, html_path = write_reports(result, tmp_path)
    assert md_path.name == f"{result.metadata.run_id}.md"
    assert html_path.suffix == ".html"
    assert "\r\n" not in md_path.read_text("utf-8", errors="strict")
