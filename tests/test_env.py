from pathlib import Path

import pytest

from touchstone_llm.env import (
    MissingAPIKeyError,
    get_api_key,
    key_status,
    load_env,
    redact_secrets,
)

FAKE_KEY = "gsk_test_1234567890abcdef"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_get_api_key_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", FAKE_KEY)
    assert get_api_key("groq") == FAKE_KEY


def test_missing_key_message_explains_fix_without_leaking() -> None:
    with pytest.raises(MissingAPIKeyError) as exc:
        get_api_key("groq")
    msg = str(exc.value)
    assert "GROQ_API_KEY" in msg
    assert ".env" in msg
    assert "https://console.groq.com/keys" in msg


def test_blank_key_counts_as_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "   ")
    with pytest.raises(MissingAPIKeyError):
        get_api_key("groq")


def test_provider_without_key_returns_none() -> None:
    assert get_api_key("ollama") is None


def test_unknown_provider_lists_known_ones() -> None:
    with pytest.raises(ValueError, match="groq"):
        get_api_key("nope")


def test_key_status_reports_booleans_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", FAKE_KEY)
    status = key_status()
    assert status["gemini"] is True
    assert status["groq"] is False
    assert FAKE_KEY not in repr(status)


def test_load_env_reads_file_without_overriding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(f"GROQ_API_KEY={FAKE_KEY}\nGEMINI_API_KEY=from-file\n", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "from-shell")
    load_env(env_file)
    assert get_api_key("groq") == FAKE_KEY
    assert get_api_key("gemini") == "from-shell"


def test_redact_secrets_masks_known_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", FAKE_KEY)
    text = f"401 Unauthorized for Bearer {FAKE_KEY}"
    assert redact_secrets(text) == "401 Unauthorized for Bearer ***"


def test_redact_secrets_ignores_short_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "a")
    assert redact_secrets("a cat") == "a cat"


def test_save_api_key_writes_private_file_and_sets_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from touchstone_llm.env import save_api_key, user_env_path

    monkeypatch.setenv("TOUCHSTONE_HOME", str(tmp_path))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    path = save_api_key("groq", "  " + FAKE_KEY + "  ")
    assert path == user_env_path() == tmp_path / ".env"
    assert get_api_key("groq") == FAKE_KEY
    save_api_key("gemini", "AIza_other_key_value_123")
    save_api_key("groq", "gsk_replaced_key_value_456")
    lines = path.read_text("utf-8").splitlines()
    assert lines.count("GROQ_API_KEY=gsk_replaced_key_value_456") == 1
    assert not any(FAKE_KEY in line for line in lines)
    assert "GEMINI_API_KEY=AIza_other_key_value_123" in lines


@pytest.mark.parametrize("bad", ["", "   ", "has space", "line\nbreak", "x" * 401])
def test_save_api_key_rejects_bad_values(
    bad: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from touchstone_llm.env import save_api_key

    monkeypatch.setenv("TOUCHSTONE_HOME", str(tmp_path))
    with pytest.raises(ValueError):
        save_api_key("groq", bad)
    assert not (tmp_path / ".env").exists()


def test_save_api_key_rejects_keyless_or_unknown_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from touchstone_llm.env import save_api_key

    monkeypatch.setenv("TOUCHSTONE_HOME", str(tmp_path))
    with pytest.raises(ValueError):
        save_api_key("ollama", FAKE_KEY)
    with pytest.raises(ValueError):
        save_api_key("nope", FAKE_KEY)


def test_load_env_reads_user_key_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOUCHSTONE_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(f"GROQ_API_KEY={FAKE_KEY}\n", encoding="utf-8")
    load_env()
    assert get_api_key("groq") == FAKE_KEY
