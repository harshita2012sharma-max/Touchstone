"""FastAPI app behind ``touchstone ui``.

Security for a local tool:
- The CLI binds to 127.0.0.1 only.
- Requests must use Host ``127.0.0.1`` or ``localhost`` (blocks DNS rebinding).
- State-changing requests from another web origin are refused (blocks CSRF).
- API keys are never returned; only "set / not set".
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator, Callable
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from touchstone_llm import __version__
from touchstone_llm.backends import available_backends, get_backend
from touchstone_llm.backends.base import Backend
from touchstone_llm.config import GenerationSettings, RunConfig
from touchstone_llm.env import (
    PROVIDER_KEYS,
    custom_server,
    key_status,
    redact_secrets,
    save_api_key,
    save_custom_server,
)
from touchstone_llm.errors import TouchstoneError
from touchstone_llm.providers import BY_NAME
from touchstone_llm.report import render_html
from touchstone_llm.results import RunResult
from touchstone_llm.server.jobs import JobBusyError, JobManager
from touchstone_llm.tasks import available_tasks, get_task
from touchstone_llm.tasks.base import DatasetError

LOCAL_HOSTS = ("127.0.0.1", "localhost")
DEFAULT_STATIC_DIR = Path(__file__).parent / "static"
_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

NOT_BUILT_PAGE = """<!doctype html><meta charset="utf-8"><title>touchstone</title>
<body style="font-family:system-ui;max-width:640px;margin:48px auto;padding:0 16px">
<h1>touchstone</h1><p>The web UI is not built in this copy of touchstone.</p>
<p>From a source checkout run <code>cd ui &amp;&amp; npm install &amp;&amp; npm run build</code>,
or install a released version with <code>pip install touchstone-llm[ui]</code>.</p>
<p>The JSON API is available at <a href="/api/status">/api/status</a>.</p></body>"""


class JobRequest(BaseModel):
    """Body of ``POST /api/jobs``."""

    model: str
    tasks: list[str] = Field(min_length=1)
    limit: int | None = Field(default=None, ge=1)
    max_tokens: int = Field(default=512, ge=1, le=8192)
    drafts: bool = False


class CustomRequest(BaseModel):
    """Body of ``POST /api/custom``: an OpenAI-compatible server address and optional key."""

    base_url: str = Field(min_length=1, max_length=300)
    key: str | None = Field(default=None, max_length=400)


def _provider_status(name: str, keys: dict[str, bool]) -> dict[str, Any]:
    """Public facts about a provider. Never includes a key value."""
    info = BY_NAME.get(name)
    needs_key = PROVIDER_KEYS.get(name) is not None
    key_set = keys.get(name, False)
    url, _key = custom_server() if name == "custom" else (None, None)
    ready = (not needs_key or key_set) if name != "custom" else url is not None
    return {
        "name": name,
        "label": info.label if info else name,
        "description": info.description if info else "",
        "group": info.group if info else "own",
        "verified": info.verified if info else False,
        "needs_key": needs_key,
        "key_set": key_set,
        "ready": ready,
        "signup_url": (pk.signup_url if (pk := PROVIDER_KEYS.get(name)) else None),
        "custom_url": url,
    }


class KeyRequest(BaseModel):
    """Body of ``POST /api/keys``. The key is saved locally and never sent back."""

    provider: str
    key: str = Field(min_length=1, max_length=400)


def _count(task_name: str, path: Path | None = None, *, drafts: bool = False) -> int:
    try:
        return len(get_task(task_name, data_path=path).load_samples(allow_unreviewed=drafts))
    except DatasetError:
        return 0


def _summary(result: RunResult) -> dict[str, Any]:
    tasks = [
        {"task": t.task, "n": t.n, "score": t.score, "unparsed_rate": t.unparsed_rate}
        for t in result.tasks
    ]
    total_n = sum(t.n for t in result.tasks)
    return {
        "run_id": result.metadata.run_id,
        "model": result.config.model,
        "provider_model_id": result.metadata.provider_model_id,
        "started_at": result.metadata.started_at.isoformat(),
        "allow_unreviewed": result.config.allow_unreviewed,
        "settings": result.config.settings.model_dump(),
        "total_n": total_n,
        "mean_score": sum(t.score for t in result.tasks) / len(result.tasks) if tasks else 0.0,
        "tasks": tasks,
    }


def create_app(
    *,
    runs_dir: Path,
    drafts_dir: Path | None = None,
    static_dir: Path | None = DEFAULT_STATIC_DIR,
    backend_factory: Callable[[str], Backend] | None = None,
    use_cache: bool = True,
) -> FastAPI:
    """Build the app. ``backend_factory`` is injectable for tests."""
    make_backend = backend_factory or (lambda provider: get_backend(provider))
    jobs = JobManager(runs_dir, use_cache=use_cache)
    app = FastAPI(title="touchstone", version=__version__, docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(LOCAL_HOSTS))

    @app.middleware("http")
    async def same_origin_writes(request: Request, call_next: Any) -> Any:
        origin = request.headers.get("origin")
        is_write = request.method not in ("GET", "HEAD", "OPTIONS")
        if is_write and origin and urlparse(origin).hostname not in LOCAL_HOSTS:
            return JSONResponse({"detail": "Cross-origin request refused."}, status_code=403)
        return await call_next(request)

    def load_run(run_id: str) -> RunResult:
        if not _RUN_ID.match(run_id):
            raise HTTPException(400, "Invalid run id.")
        path = (runs_dir / f"{run_id}.json").resolve()
        if path.parent != runs_dir.resolve() or not path.is_file():
            raise HTTPException(404, "Run not found.")
        return RunResult.load(path)

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        keys = key_status()
        has_drafts = drafts_dir is not None and drafts_dir.is_dir()
        return {
            "version": __version__,
            "providers": [_provider_status(name, keys) for name in available_backends()],
            "tasks": [
                {
                    "name": name,
                    "version": get_task(name).version,
                    "description": get_task(name).description,
                    "items": _count(name),
                    "draft_items": _count(name, drafts_dir / f"{name}.jsonl", drafts=True)
                    if has_drafts and drafts_dir
                    else 0,
                }
                for name in available_tasks()
            ],
            "settings": GenerationSettings().model_dump(),
            "drafts_available": has_drafts,
        }

    @app.post("/api/keys")
    def save_key(body: KeyRequest) -> dict[str, Any]:
        try:
            save_api_key(body.provider, body.key)
        except ValueError as err:
            raise HTTPException(400, str(err)) from None
        return {"provider": body.provider, "key_set": True}

    @app.post("/api/custom")
    def save_custom(body: CustomRequest) -> dict[str, Any]:
        try:
            save_custom_server(body.base_url, body.key)
        except ValueError as err:
            raise HTTPException(400, str(err)) from None
        url, _key = custom_server()
        return {"provider": "custom", "ready": True, "custom_url": url}

    @app.get("/api/models/{provider}")
    def models(provider: str) -> dict[str, Any]:
        try:
            backend = make_backend(provider)
            try:
                ids = backend.list_models()
            finally:
                backend.close()
        except TouchstoneError as err:
            raise HTTPException(400, redact_secrets(str(err))) from None
        return {"provider": provider, "models": ids, "as_of": date.today().isoformat()}

    @app.get("/api/runs")
    def list_runs() -> dict[str, Any]:
        runs = []
        for path in runs_dir.glob("*.json") if runs_dir.is_dir() else []:
            try:
                runs.append(_summary(RunResult.load(path)))
            except (ValidationError, ValueError, OSError):
                continue  # not a touchstone result; ignore
        runs.sort(key=lambda r: r["started_at"], reverse=True)
        return {"runs": runs}

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> Any:
        return json.loads(load_run(run_id).model_dump_json())

    @app.get("/api/runs/{run_id}/report", response_class=HTMLResponse)
    def get_report(run_id: str) -> str:
        return render_html(load_run(run_id))

    @app.post("/api/jobs", status_code=202)
    def start_job(body: JobRequest) -> dict[str, str]:
        unknown = [t for t in body.tasks if t not in available_tasks()]
        if unknown:
            raise HTTPException(400, f"Unknown task(s): {', '.join(unknown)}")
        if body.drafts and drafts_dir is None:
            raise HTTPException(400, "No drafts folder is configured.")
        try:
            config = RunConfig(
                model=body.model,
                tasks=body.tasks,
                limit=body.limit,
                settings=GenerationSettings(max_tokens=body.max_tokens),
                data_dir=str(drafts_dir) if body.drafts and drafts_dir else None,
                allow_unreviewed=body.drafts,
            )
        except ValidationError as err:
            msg = "; ".join(str(e["msg"]).removeprefix("Value error, ") for e in err.errors())
            raise HTTPException(400, msg) from None
        try:
            backend = make_backend(config.model_ref.provider)
            job_id = jobs.start(config, backend)
        except JobBusyError as err:
            raise HTTPException(409, str(err)) from None
        except TouchstoneError as err:
            raise HTTPException(400, redact_secrets(str(err))) from None
        return {"job_id": job_id}

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        snap = jobs.get(job_id)
        if snap is None:
            raise HTTPException(404, "Job not found.")
        return snap

    @app.get("/api/jobs/{job_id}/events")
    async def job_events(job_id: str) -> StreamingResponse:
        if jobs.get(job_id) is None:
            raise HTTPException(404, "Job not found.")

        async def stream() -> AsyncIterator[str]:
            last = None
            while True:
                snap = jobs.get(job_id)
                if snap != last:
                    last = snap
                    yield f"data: {json.dumps(snap, ensure_ascii=False)}\n\n"
                if snap is None or snap["state"] != "running":
                    return
                await asyncio.sleep(0.25)

        return StreamingResponse(stream(), media_type="text/event-stream")

    _mount_ui(app, static_dir)
    return app


def _mount_ui(app: FastAPI, static_dir: Path | None) -> None:
    """Serve the built React app, falling back to index.html for client routes."""
    index = static_dir / "index.html" if static_dir else None
    root = static_dir.resolve() if static_dir else None

    @app.get("/{path:path}", include_in_schema=False)
    def ui(path: str) -> Any:
        if path.startswith("api/"):
            raise HTTPException(404, "Not found.")
        if root is None or index is None or not index.is_file():
            return HTMLResponse(NOT_BUILT_PAGE)
        candidate = (root / path).resolve()
        if path and candidate.is_file() and root in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index)
