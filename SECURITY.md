# Security policy

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's private vulnerability reporting ("Report a vulnerability" in the Security tab of this repository).

## How kasauti handles secrets

- API keys are read only from environment variables or a local `.env` file.
- Keys are never printed, logged or written into result files.
- kasauti collects no telemetry.
- The optional local web UI listens on `127.0.0.1` only.
