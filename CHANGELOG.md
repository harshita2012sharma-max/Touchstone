# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-11-19

### Added
- Test models from any provider with your own key: Google Gemini, Groq, OpenRouter, Hugging Face, OpenAI, Anthropic (Claude), Mistral, DeepSeek, xAI, Together AI, Ollama, plus a **Custom server** option for any OpenAI-compatible address (company endpoints, LM Studio, vLLM, other providers).
- Type any model name yourself when it is not in the provider's list.
- If a provider rejects one of the fixed settings (for example a model that refuses `temperature`, or wants `max_completion_tokens`), the request is retried without it and the change is recorded in the result and reports ("Provider adjustments").
- Redesigned New test page: providers grouped (free, paid, on this computer, your own server), key and server forms in place, more spacing and a calmer, more professional layout across all pages.

### Notes
- Providers marked "beta" use the standard request formats and are covered by tests, but have not yet been confirmed against the live service by the maintainers.

## [0.1.2] - 2026-11-19

### Added
- `python -m touchstone_llm ui` (and every other command via `python -m touchstone_llm ...`). It works even when pip's Scripts folder is not on PATH, which is common on Windows and caused "touchstone is not recognized".
- README quickstart now uses `python -m`, plus a "Something went wrong?" table for the usual setup problems (Python missing or too old, command not recognized, browser cannot connect).
- CI checks the documented start command on Windows and Linux.

## [0.1.1] - 2026-11-19

### Fixed
- `touchstone ui` no longer fails when port 7860 is already in use (for example when the UI is already open): it picks the next free port and says which one.
- The browser now opens only after the server is ready, so the first page load no longer shows a connection error.

## [0.1.0] - 2026-11-19

First public release (alpha). Questions are still drafts under review, so no official results are published.

### Added
- Two-step start for users: `pip install "touchstone-llm[ui]"` then `touchstone ui`.
- Draft questions (150, 25 per task) ship inside the package as a separate "drafts" set. They are used only on request (`--drafts`, or "Use draft questions" in the UI), and every result made with them is marked as a practice run.
- API keys can be pasted into the web UI. They are saved only on this computer in `~/.touchstone/.env` (owner-only permissions where supported), never shown again, and never logged.
- Web UI redesign: warm beige and navy theme, clear buttons, even spacing, and plain-language help on every page (how-it-works steps, hints under each option, glossary, friendly topic names).
- Project scaffold: packaging, CLI entry point with `--version`, lint/type/test tooling, CI, and community files.
- `RunConfig` with fixed defaults (temperature 0, seed 42) and `provider/model` parsing.
- API key loading from env or `.env`, with step-by-step messages when a key is missing and masking of keys in any shown text.
- Model backends: Groq, OpenRouter and Ollama (one OpenAI-compatible client), Gemini (REST), and an offline `mock` backend. Plugins can add providers via the `touchstone_llm.backends` entry point.
- Client-side rate limiting and retries with backoff for free tiers; clear errors for retired model ids, rejected keys and an unreachable Ollama server.
- Rule-based scorers: MCQ answer parser (many answer styles, ambiguous answers marked "unparsed"), numeric answer extraction (Devanagari digits, Indian digit grouping), dependency-free chrF verified against sacreBLEU, and instruction rule checks.
- Task framework with the six v1 tasks and a `touchstone_llm.tasks` entry point for plugins. Items are validated on load: CC-BY-4.0 only, at least two reviewers besides the author, unique ids.
- Dataset review workflow (`python -m touchstone_llm.review check|export|import|promote`) with CSV sheets for non-technical reviewers.
- Batch 1 drafts: 10 pending items per task (60 total), awaiting human review; none are scored yet.
- `touchstone run`: runs tasks one sample at a time, prints a score table (score, unparsed rate, latency, settings, date) and saves the full result JSON. Any failed call stops the run; replies are cached in `.touchstone/cache.sqlite`, so the same command resumes.
- `touchstone list-tasks` and `touchstone list-models <provider>` (live model ids from the provider).
- `--data-dir` and `--allow-unreviewed` for trying draft items; such runs are clearly marked "UNREVIEWED".
- `contains_any` rule check; dataset test that trivial replies ("A", "ok", "I don't know.") never pass an instruction item.
- Reports: every run also writes a self-contained HTML page (offline, light/dark, all prompts and outputs, "only wrong items" filter) and a Markdown summary. Model output is HTML-escaped. `touchstone report <result.json>` rebuilds them.
- `touchstone reproduce <result.json>`: reruns the exact config and checks that prompts and settings are identical, then compares scores and outputs.
- `touchstone ui` (optional `[ui]` extra): local FastAPI server on 127.0.0.1 with a JSON API for status, live model lists, saved runs, reports, and background runs with live progress (SSE). Host and Origin checks block DNS rebinding and cross-site requests; API keys are only reported as set or not set.
- Web UI (React, built into the wheel so users need no Node): Runs list, New run (live model list, key status, draft toggle, fixed settings), live progress, run results with a "touchstone" hero (mean score, gold streak bars, strongest/hardest task with ties shown as ties, toughest item), item explorer with filters, Compare (up to 3 runs, colorblind-validated colors, value labels and table view, warnings when settings, items or dates differ), and About. Light and dark themes, self-hosted fonts with Devanagari, reduced-motion support.
- CI job that builds the UI and wheel, checks that no `.env` or unreviewed data ships, and smoke-tests a clean install.
- Full README (quickstart, tasks, fairness and reproducibility, limitations, data and safety, related work with verified citations), `CITATION.cff`, and a tag-triggered release workflow using PyPI Trusted Publishing (TestPyPI first).
- Packaging fix: the built web UI now ships in the sdist too, so wheels built from the sdist include it; CI builds the same way as the release.
- Design system for the web UI in `design-system/touchstone/MASTER.md` (generated with ui-ux-pro-max, adapted for Devanagari and neutral comparisons).
- Result schema (`RunResult`) that saves every prompt, output, score and setting as readable UTF-8 JSON.
