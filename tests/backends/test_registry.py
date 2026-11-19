import pytest

from touchstone_llm.backends import available_backends, get_backend
from touchstone_llm.backends.mock import MockBackend
from touchstone_llm.backends.openai_compat import OpenAICompatBackend
from touchstone_llm.config import GenerationSettings
from touchstone_llm.env import MissingAPIKeyError
from touchstone_llm.errors import TouchstoneError


def test_builtin_backends_listed() -> None:
    assert {"groq", "gemini", "openrouter", "ollama", "mock"} <= set(available_backends())


def test_unknown_provider_error_lists_known() -> None:
    with pytest.raises(TouchstoneError, match="groq"):
        get_backend("nope")


def test_groq_needs_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError):
        get_backend("groq")


def test_groq_built_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_value")
    backend = get_backend("groq")
    assert isinstance(backend, OpenAICompatBackend)
    assert backend.name == "groq"


def test_ollama_uses_env_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:9999/")
    backend = get_backend("ollama")
    assert isinstance(backend, OpenAICompatBackend)
    assert backend.base_url == "http://127.0.0.1:9999/v1"


def test_mock_backend_is_deterministic() -> None:
    backend = get_backend("mock")
    assert isinstance(backend, MockBackend)
    a = backend.generate("echo", "hello", GenerationSettings())
    b = backend.generate("echo", "hello", GenerationSettings())
    assert a.text == b.text == "hello"
    assert backend.list_models() == ["echo", "fixed"]


def test_mock_fixed_reply_and_scripted() -> None:
    backend = MockBackend(replies={"q1": "B"})
    assert backend.generate("fixed", "anything", GenerationSettings()).text == "A"
    assert backend.generate("echo", "q1", GenerationSettings()).text == "B"
