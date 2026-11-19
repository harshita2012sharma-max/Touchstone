"""Open the touchstone web UI inside Google Colab.

In a Colab cell::

    !pip install -q "touchstone-llm[ui]"
    from touchstone_llm.colab import launch
    launch()

The server runs in the background on the Colab machine (127.0.0.1 only).
Colab's own proxy gives the user a private link to it; only the Google account
running the notebook can open that link. Colab's proxy rewrites the Host header,
so the Host check is off here; changes (saving keys, starting tests) are still
accepted only from that link's page.

Keys typed into the UI are saved on the Colab machine, which Google wipes when
the session ends.
"""

from __future__ import annotations

import html
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from touchstone_llm.errors import TouchstoneError

_NOT_COLAB = (
    "touchstone_llm.colab.launch() works only inside Google Colab. "
    "On your own computer run: python -m touchstone_llm ui"
)
_running: Any = None


def _colab_proxy_url(port: int) -> str:
    """Ask Colab for the private proxy URL of ``port`` on this machine."""
    try:
        from google.colab.output import eval_js  # type: ignore[import-not-found]
    except ImportError:
        raise TouchstoneError(_NOT_COLAB) from None
    return str(eval_js(f"google.colab.kernel.proxyPort({int(port)}, {{cache: false}})"))


def _show_link(url: str) -> None:
    """Print the link, and show a clickable one when IPython is available."""
    print(f"touchstone UI: {url}")
    try:
        from IPython.display import HTML, display  # type: ignore[import-not-found]
    except ImportError:
        return
    safe = html.escape(url, quote=True)
    display(
        HTML(
            f'<a href="{safe}" target="_blank" rel="noopener" '
            'style="font-size:16px;font-weight:600">Open touchstone</a>'
            "<p style='font-size:13px'>Only your Google account can open this link. "
            "Keys you save are wiped when this Colab session ends.</p>"
        )
    )


def stop() -> None:
    """Stop the UI server started by :func:`launch`, if any."""
    global _running
    if _running is not None:
        _running.should_exit = True
        _running = None


def launch(
    port: int = 7860,
    runs_dir: str | Path = "runs",
    *,
    timeout: float = 20.0,
) -> str:
    """Start the UI in the background and return its private Colab link."""
    global _running
    try:
        import uvicorn

        from touchstone_llm.server.app import create_app
    except ImportError:
        raise TouchstoneError(
            'The web UI needs extra packages: pip install "touchstone-llm[ui]"'
        ) from None
    from touchstone_llm.cli import PORT_TRIES, find_free_port
    from touchstone_llm.drafts import default_drafts_dir
    from touchstone_llm.env import load_env

    stop()
    free = find_free_port(port)
    if free is None:
        raise TouchstoneError(f"Ports {port}-{port + PORT_TRIES - 1} are all busy.")
    url = _colab_proxy_url(free)
    host = urlparse(url).hostname
    if not host or urlparse(url).scheme != "https":
        raise TouchstoneError(f"Colab returned an unexpected link: {url!r}")

    load_env()
    runs = Path(runs_dir)
    runs.mkdir(parents=True, exist_ok=True)
    app = create_app(runs_dir=runs, drafts_dir=default_drafts_dir(), colab_host=host)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=free, log_level="warning"))
    threading.Thread(target=server.run, name="touchstone-ui", daemon=True).start()

    deadline = time.monotonic() + timeout
    while not server.started:
        if time.monotonic() > deadline:
            server.should_exit = True
            raise TouchstoneError("The touchstone UI did not start in time. Run launch() again.")
        time.sleep(0.1)
    _running = server
    _show_link(url)
    return url
