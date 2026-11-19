# Security policy

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's private vulnerability reporting ("Report a vulnerability" in the Security tab of this repository).

## How touchstone handles secrets

- API keys are read only from environment variables, a local `.env` file, or the private key file `~/.touchstone/.env` that the web UI writes when you paste a key (owner-only permissions where the OS supports it).
- Keys are never printed, logged or written into result files.
- touchstone collects no telemetry.
- The optional local web UI listens on `127.0.0.1` only.
