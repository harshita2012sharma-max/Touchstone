"""API key handling.

Keys come only from environment variables or a local ``.env`` file. This
module never prints, logs or returns key values except to the backend that
needs them, and :func:`redact_secrets` masks them in any text we show.
"""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from touchstone_llm.errors import TouchstoneError


@dataclass(frozen=True)
class ProviderKey:
    """Where a provider's API key lives and where users can create one."""

    env_var: str
    signup_url: str


PROVIDER_KEYS: dict[str, ProviderKey | None] = {
    "groq": ProviderKey("GROQ_API_KEY", "https://console.groq.com/keys"),
    "gemini": ProviderKey("GEMINI_API_KEY", "https://aistudio.google.com/apikey"),
    "openrouter": ProviderKey("OPENROUTER_API_KEY", "https://openrouter.ai/keys"),
    "ollama": None,  # local, no key needed
}

_MIN_SECRET_LEN = 8  # shorter values are too likely to match normal text


class MissingAPIKeyError(TouchstoneError):
    """Raised when a provider needs an API key that is not set."""

    def __init__(self, provider: str, key: ProviderKey) -> None:
        """Build a message that explains exactly how to set the key."""
        super().__init__(
            f"No API key found for '{provider}'.\n"
            f"  1. Create a free key at {key.signup_url}\n"
            f"  2. Add this line to a file named .env in your project folder:\n"
            f"       {key.env_var}=your-key-here\n"
            f"     or set it in your shell, e.g. `export {key.env_var}=...` "
            f'(PowerShell: `$env:{key.env_var}="..."`).\n'
            f"Keep .env out of git; touchstone never prints your key."
        )


def user_env_path() -> Path:
    """Private key file in the user's home folder (``TOUCHSTONE_HOME`` overrides the folder)."""
    home = os.environ.get("TOUCHSTONE_HOME", "").strip()
    return (Path(home) if home else Path.home() / ".touchstone") / ".env"


def load_env(path: str | Path | None = None) -> None:
    """Load keys from a ``.env`` file and from the user's key file.

    Order of priority: the shell environment, then ``path`` (or a ``.env`` found
    from the current folder), then the key file saved from the web UI.
    """
    dotenv_path = Path(path) if path is not None else find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)
    user_file = user_env_path()
    if user_file.is_file():
        load_dotenv(user_file, override=False)


_MAX_KEY_LEN = 400


def save_api_key(provider: str, value: str) -> Path:
    """Save a provider's key to the user's private key file and use it right away.

    The value is never returned or logged. Raises ``ValueError`` for an unknown
    provider, a provider that needs no key, or a value that is empty, too long,
    or contains spaces or line breaks.
    """
    key = _provider_key(provider)
    if key is None:
        raise ValueError(f"'{provider}' does not need an API key.")
    value = value.strip()
    if not value or len(value) > _MAX_KEY_LEN or any(ch.isspace() for ch in value):
        raise ValueError(
            "That does not look like an API key (it is empty, too long, or has spaces)."
        )
    path = user_env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text("utf-8").splitlines() if path.is_file() else []
    kept = [ln for ln in lines if not ln.strip().startswith(f"{key.env_var}=")]
    kept.append(f"{key.env_var}={value}")
    path.write_text("\n".join(kept) + "\n", encoding="utf-8", newline="\n")
    with contextlib.suppress(OSError):
        path.chmod(0o600)  # owner read/write only (no effect on Windows)
    os.environ[key.env_var] = value
    return path


def _provider_key(provider: str) -> ProviderKey | None:
    try:
        return PROVIDER_KEYS[provider]
    except KeyError:
        known = ", ".join(sorted(PROVIDER_KEYS))
        raise ValueError(f"Unknown provider '{provider}'. Known providers: {known}.") from None


def get_api_key(provider: str) -> str | None:
    """Return the API key for ``provider``, or ``None`` if it needs no key.

    Raises:
        MissingAPIKeyError: the provider needs a key and it is unset or blank.
        ValueError: the provider is unknown.

    """
    key = _provider_key(provider)
    if key is None:
        return None
    value = os.environ.get(key.env_var, "").strip()
    if not value:
        raise MissingAPIKeyError(provider, key)
    return value


def key_status() -> dict[str, bool]:
    """Return ``{provider: is_key_set}`` for providers that need keys. Never includes values."""
    return {
        name: bool(os.environ.get(key.env_var, "").strip())
        for name, key in PROVIDER_KEYS.items()
        if key is not None
    }


def redact_secrets(text: str) -> str:
    """Replace any configured API key value found in ``text`` with ``***``."""
    for key in PROVIDER_KEYS.values():
        if key is None:
            continue
        value = os.environ.get(key.env_var, "").strip()
        if len(value) >= _MIN_SECRET_LEN:
            text = text.replace(value, "***")
    return text
