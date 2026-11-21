"""Entry point for the public online demo (a Hugging Face Space).

Run with ``python -m touchstone_llm.space``. The app is started in demo mode:
only the keyless practice model is offered, and saving API keys or a custom
server is refused, so visitors never leave secrets on a shared machine.
Everything else (the UI, reports, comparing runs) works as on a laptop.

Never use this to serve real providers publicly; use ``touchstone ui`` locally.
"""

from __future__ import annotations

import os
from pathlib import Path

PUBLIC_HOSTS = ("*.hf.space",)


def main() -> None:
    """Start the demo server on all interfaces (inside the Space container)."""
    import uvicorn

    from touchstone_llm.drafts import default_drafts_dir
    from touchstone_llm.server.app import create_app

    runs_dir = Path(os.environ.get("TOUCHSTONE_RUNS_DIR", "/tmp/touchstone-runs"))
    runs_dir.mkdir(parents=True, exist_ok=True)
    app = create_app(
        runs_dir=runs_dir,
        drafts_dir=default_drafts_dir(),
        demo=True,
        public_hosts=PUBLIC_HOSTS,
    )
    port = int(os.environ.get("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")  # inside the Space container


if __name__ == "__main__":
    main()
