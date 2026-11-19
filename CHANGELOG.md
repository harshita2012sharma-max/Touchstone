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
- Result schema (`RunResult`) that saves every prompt, output, score and setting as readable UTF-8 JSON.
