# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project scaffold: packaging, CLI entry point with `--version`, lint/type/test tooling, CI, and community files.
- `RunConfig` with fixed defaults (temperature 0, seed 42) and `provider/model` parsing.
- API key loading from env or `.env`, with step-by-step messages when a key is missing and masking of keys in any shown text.
- Model backends: Groq, OpenRouter and Ollama (one OpenAI-compatible client), Gemini (REST), and an offline `mock` backend. Plugins can add providers via the `kasauti.backends` entry point.
- Client-side rate limiting and retries with backoff for free tiers; clear errors for retired model ids, rejected keys and an unreachable Ollama server.
- Rule-based scorers: MCQ answer parser (many answer styles, ambiguous answers marked "unparsed"), numeric answer extraction (Devanagari digits, Indian digit grouping), dependency-free chrF verified against sacreBLEU, and instruction rule checks.
- Task framework with the six v1 tasks and a `kasauti.tasks` entry point for plugins. Items are validated on load: CC-BY-4.0 only, at least two reviewers besides the author, unique ids.
- Dataset review workflow (`python -m kasauti.review check|export|import|promote`) with CSV sheets for non-technical reviewers.
- Batch 1 drafts: 10 pending items per task (60 total), awaiting human review; none are scored yet.
- `kasauti run`: runs tasks one sample at a time, prints a score table (score, unparsed rate, latency, settings, date) and saves the full result JSON. Any failed call stops the run; replies are cached in `.kasauti/cache.sqlite`, so the same command resumes.
- `kasauti list-tasks` and `kasauti list-models <provider>` (live model ids from the provider).
- `--data-dir` and `--allow-unreviewed` for trying draft items; such runs are clearly marked "UNREVIEWED".
- `contains_any` rule check; dataset test that trivial replies ("A", "ok", "I don't know.") never pass an instruction item.
- Reports: every run also writes a self-contained HTML page (offline, light/dark, all prompts and outputs, "only wrong items" filter) and a Markdown summary. Model output is HTML-escaped. `kasauti report <result.json>` rebuilds them.
- `kasauti reproduce <result.json>`: reruns the exact config and checks that prompts and settings are identical, then compares scores and outputs.
- Result schema (`RunResult`) that saves every prompt, output, score and setting as readable UTF-8 JSON.
