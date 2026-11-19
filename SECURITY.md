# Security policy

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's private vulnerability reporting ("Report a vulnerability" in the Security tab of this repository).

## How touchstone handles secrets

- API keys are read only from environment variables or a local `.env` file.
- Keys are never printed, logged or written into result files.
- touchstone collects no telemetry.
- The optional local web UI listens on `127.0.0.1` only.
