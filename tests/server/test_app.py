import json
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from conftest import CountingMock
from touchstone_llm.config import RunConfig
from touchstone_llm.runner import Runner
from touchstone_llm.server.app import create_app

KEY = "gsk_server_test_secret_123456"


@pytest.fixture
def runs_dir(tmp_path: Path, data_dir: Path) -> Path:
    out = tmp_path / "runs"
    cfg = RunConfig(model="mock/fixed", tasks=["hindi_reasoning"], data_dir=str(data_dir))
    Runner(cfg, backend=CountingMock(), cache=None).run().save(out)
    return out


@pytest.fixture
def client(runs_dir: Path, data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("GROQ_API_KEY", KEY)
    app = create_app(
        runs_dir=runs_dir,
        drafts_dir=data_dir,
        backend_factory=lambda provider: CountingMock(),
        use_cache=False,
    )
    return TestClient(app, base_url="http://127.0.0.1:7860")


def test_status_shows_key_presence_not_value(client: TestClient) -> None:
    res = client.get("/api/status")
    assert res.status_code == 200
    body = res.json()
    assert KEY not in res.text
    groq = next(p for p in body["providers"] if p["name"] == "groq")
    assert groq == {"name": "groq", "needs_key": True, "key_set": True}
    assert {t["name"] for t in body["tasks"]} >= {"hindi_reasoning", "cultural_context"}
    assert body["settings"]["temperature"] == 0.0
    assert body["drafts_available"] is True


def test_list_and_get_runs(client: TestClient) -> None:
    runs = client.get("/api/runs").json()["runs"]
    assert len(runs) == 1
    summary = runs[0]
    assert summary["model"] == "mock/fixed"
    assert summary["tasks"][0]["task"] == "hindi_reasoning"
    assert summary["total_n"] == 3
    full = client.get(f"/api/runs/{summary['run_id']}").json()
    assert full["tasks"][0]["samples"][0]["prompt"].startswith("1 + 1")
    report = client.get(f"/api/runs/{summary['run_id']}/report")
    assert report.headers["content-type"].startswith("text/html")


@pytest.mark.parametrize("bad", ["..%2F..%2Fsecret", "nope", "a b"])
def test_run_id_is_validated(client: TestClient, bad: str) -> None:
    assert client.get(f"/api/runs/{bad}").status_code in (400, 404)


def test_foreign_host_rejected(runs_dir: Path) -> None:
    app = create_app(runs_dir=runs_dir, backend_factory=lambda p: CountingMock(), use_cache=False)
    evil = TestClient(app, base_url="http://evil.example")
    assert evil.get("/api/status").status_code == 400


def test_cross_origin_post_rejected(client: TestClient) -> None:
    res = client.post(
        "/api/jobs",
        json={"model": "mock/fixed", "tasks": ["hindi_reasoning"]},
        headers={"Origin": "https://evil.example"},
    )
    assert res.status_code == 403


def _wait(client: TestClient, job_id: str) -> dict:
    for _ in range(100):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["state"] in ("done", "failed"):
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_start_job_runs_and_saves(client: TestClient, runs_dir: Path) -> None:
    res = client.post(
        "/api/jobs",
        json={"model": "mock/fixed", "tasks": ["hindi_reasoning"], "drafts": True},
        headers={"Origin": "http://127.0.0.1:7860"},
    )
    assert res.status_code == 202, res.text
    job = _wait(client, res.json()["job_id"])
    assert job["state"] == "done", job
    assert job["progress"]["hindi_reasoning"] == {"done": 3, "total": 3}
    assert (runs_dir / f"{job['run_id']}.json").is_file()
    assert (runs_dir / f"{job['run_id']}.html").is_file()
    saved = json.loads((runs_dir / f"{job['run_id']}.json").read_text("utf-8"))
    assert saved["config"]["data_dir"] is not None


def test_job_events_stream(client: TestClient) -> None:
    job_id = client.post(
        "/api/jobs",
        json={"model": "mock/fixed", "tasks": ["hindi_reasoning"], "drafts": True},
    ).json()["job_id"]
    with client.stream("GET", f"/api/jobs/{job_id}/events") as stream:
        lines = [line for line in stream.iter_lines() if line.startswith("data:")]
    events = [json.loads(line.removeprefix("data:")) for line in lines]
    assert events[-1]["state"] == "done"


def test_bad_job_request_is_400(client: TestClient) -> None:
    res = client.post("/api/jobs", json={"model": "nomodel", "tasks": ["hindi_reasoning"]})
    assert res.status_code == 400
    assert "provider/model" in res.json()["detail"]


def test_failed_job_reports_redacted_error(runs_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from touchstone_llm.backends.base import AuthError

    monkeypatch.setenv("GROQ_API_KEY", KEY)
    app = create_app(
        runs_dir=runs_dir,
        drafts_dir=None,
        backend_factory=lambda p: CountingMock(fail=AuthError(f"bad key {KEY}")),
        use_cache=False,
    )
    client = TestClient(app, base_url="http://127.0.0.1:7860")
    res = client.post("/api/jobs", json={"model": "mock/fixed", "tasks": ["hindi_reasoning"]})
    job = _wait(client, res.json()["job_id"])
    assert job["state"] == "failed"
    assert KEY not in job["error"]


def test_spa_fallback_when_built(tmp_path: Path, runs_dir: Path) -> None:
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("<!doctype html><title>touchstone</title>", "utf-8")
    app = create_app(runs_dir=runs_dir, static_dir=static, use_cache=False)
    c = TestClient(app, base_url="http://127.0.0.1:7860")
    assert "touchstone" in c.get("/").text
    assert "touchstone" in c.get("/runs/some-id").text  # client-side route


def test_helpful_page_when_ui_not_built(runs_dir: Path, tmp_path: Path) -> None:
    app = create_app(runs_dir=runs_dir, static_dir=tmp_path / "missing", use_cache=False)
    c = TestClient(app, base_url="http://127.0.0.1:7860")
    assert "not built" in c.get("/").text
