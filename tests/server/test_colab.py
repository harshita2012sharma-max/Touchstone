from __future__ import annotations

from pathlib import Path

import httpx
import pytest

pytest.importorskip("uvicorn")

from touchstone_llm import colab
from touchstone_llm.errors import TouchstoneError
from touchstone_llm.server.app import create_app

PROXY = "https://7861-m-s-abc123-b.us-west1-1.prod.colab.dev/"
PROXY_HOST = "7861-m-s-abc123-b.us-west1-1.prod.colab.dev"


def test_launch_outside_colab_says_how_to_run_locally(tmp_path: Path) -> None:
    with pytest.raises(TouchstoneError, match="python -m touchstone_llm ui"):
        colab.launch(port=7920, runs_dir=tmp_path)


def test_launch_serves_ui_through_the_colab_proxy_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("TOUCHSTONE_HOME", str(tmp_path / "home"))
    ports: list[int] = []

    def fake_proxy(port: int) -> str:
        ports.append(port)
        return PROXY

    monkeypatch.setattr(colab, "_colab_proxy_url", fake_proxy)
    try:
        assert colab.launch(port=7930, runs_dir=tmp_path / "runs") == PROXY
        assert PROXY in capsys.readouterr().out
        base = f"http://127.0.0.1:{ports[0]}"
        ok = httpx.get(f"{base}/api/status", headers={"Host": PROXY_HOST})
        assert ok.status_code == 200
        assert httpx.get(f"{base}/api/status").status_code == 200
        evil = httpx.get(f"{base}/api/status", headers={"Host": "evil.example"})
        assert evil.status_code == 400
        write = httpx.post(
            f"{base}/api/keys",
            json={"provider": "groq", "key": "x" * 20},
            headers={"Host": PROXY_HOST, "Origin": "https://evil.example"},
        )
        assert write.status_code == 403
    finally:
        colab.stop()


def test_launch_refuses_a_non_https_proxy_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(colab, "_colab_proxy_url", lambda port: "http://example.com/")
    with pytest.raises(TouchstoneError, match="unexpected link"):
        colab.launch(port=7940, runs_dir=tmp_path)


def test_extra_hosts_must_be_exact(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exact"):
        create_app(runs_dir=tmp_path, static_dir=None, extra_hosts=("*.colab.dev",))
