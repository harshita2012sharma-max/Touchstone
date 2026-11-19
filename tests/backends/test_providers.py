import json
from pathlib import Path

import httpx
import pytest
import respx

from touchstone_llm.backends import available_backends, get_backend
from touchstone_llm.backends.anthropic import ANTHROPIC_BASE_URL, AnthropicBackend
from touchstone_llm.backends.base import AuthError, ModelNotFoundError
from touchstone_llm.backends.openai_compat import OpenAICompatBackend
from touchstone_llm.config import GenerationSettings
from touchstone_llm.env import PROVIDER_KEYS, save_custom_server
from touchstone_llm.errors import TouchstoneError
from touchstone_llm.providers import CATALOG

BASE = "https://api.example.test/v1"


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOUCHSTONE_HOME", str(tmp_path / "home"))
    for p in CATALOG:
        if p.env_var:
            monkeypatch.delenv(p.env_var, raising=False)
    monkeypatch.delenv("CUSTOM_BASE_URL", raising=False)
    monkeypatch.delenv("CUSTOM_API_KEY", raising=False)


def test_catalog_lists_all_providers() -> None:
    names = available_backends()
    for expected in (
        "gemini",
        "groq",
        "openrouter",
        "huggingface",
        "openai",
        "anthropic",
        "mistral",
        "deepseek",
        "xai",
        "together",
        "ollama",
        "custom",
        "mock",
    ):
        assert expected in names
    assert len(names) == len(set(names))


@pytest.mark.parametrize(
    "p", [p for p in CATALOG if PROVIDER_KEYS.get(p.name)], ids=lambda p: p.name
)
def test_every_keyed_provider_builds_with_its_own_key(p, monkeypatch: pytest.MonkeyPatch) -> None:
    from touchstone_llm.env import MissingAPIKeyError

    with pytest.raises(MissingAPIKeyError):
        get_backend(p.name)
    monkeypatch.setenv(p.env_var, "user_own_key_123456")
    backend = get_backend(p.name)
    assert backend.name == p.name
    assert p.signup_url and p.signup_url.startswith("https://")


def test_anthropic_request_and_reply() -> None:
    backend = AnthropicBackend(
        api_key="sk-ant-test-123456", requests_per_minute=None, max_attempts=1
    )
    with respx.mock:
        route = respx.post(f"{ANTHROPIC_BASE_URL}/messages").mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "claude-test-1",
                    "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": "उत्तर: "}, {"type": "text", "text": "B"}],
                },
            )
        )
        out = backend.generate("claude-test", "प्रश्न", GenerationSettings())
    assert out.text == "उत्तर: B"
    assert out.model_id == "claude-test-1"
    assert any("seed" in n for n in out.notes)
    req = route.calls.last.request
    assert req.headers["x-api-key"] == "sk-ant-test-123456"
    assert req.headers["anthropic-version"]
    body = json.loads(req.content)
    assert body == {
        "model": "claude-test",
        "max_tokens": 512,
        "temperature": 0.0,
        "messages": [{"role": "user", "content": "प्रश्न"}],
    }


@respx.mock
def test_anthropic_errors_and_model_list() -> None:
    backend = AnthropicBackend(
        api_key="sk-ant-test-123456", requests_per_minute=None, max_attempts=1
    )
    respx.post(f"{ANTHROPIC_BASE_URL}/messages").mock(
        side_effect=[
            httpx.Response(401, json={"error": {"message": "invalid x-api-key"}}),
            httpx.Response(404, json={"error": {"message": "model: old"}}),
        ]
    )
    with pytest.raises(AuthError):
        backend.generate("m", "p", GenerationSettings())
    with pytest.raises(ModelNotFoundError):
        backend.generate("old", "p", GenerationSettings())
    respx.get(f"{ANTHROPIC_BASE_URL}/models").mock(
        side_effect=[
            httpx.Response(200, json={"data": [{"id": "b"}], "has_more": True, "last_id": "b"}),
            httpx.Response(200, json={"data": [{"id": "a"}], "has_more": False}),
        ]
    )
    assert backend.list_models() == ["a", "b"]


def _compat() -> OpenAICompatBackend:
    return OpenAICompatBackend(
        name="openai",
        base_url=BASE,
        api_key="k_test_123456",
        requests_per_minute=None,
        max_attempts=1,
    )


@respx.mock
def test_rejected_settings_are_dropped_and_recorded() -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        side_effect=[
            httpx.Response(
                400,
                json={
                    "error": {
                        "message": "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead."
                    }
                },
            ),
            httpx.Response(
                400,
                json={
                    "error": {
                        "message": "Unsupported value: 'temperature' does not support 0 with this model."
                    }
                },
            ),
            httpx.Response(200, json={"model": "m-1", "choices": [{"message": {"content": "B"}}]}),
            httpx.Response(200, json={"model": "m-1", "choices": [{"message": {"content": "C"}}]}),
        ]
    )
    backend = _compat()
    out = backend.generate("m", "p", GenerationSettings())
    assert out.text == "B"
    final = json.loads(route.calls[2].request.content)
    assert "max_tokens" not in final and final["max_completion_tokens"] == 512
    assert "temperature" not in final
    assert any("max_completion_tokens" in n for n in out.notes)
    assert any("'temperature'" in n for n in out.notes)
    # later calls start with the adjusted request straight away
    backend.generate("m", "p2", GenerationSettings())
    assert route.call_count == 4


@respx.mock
def test_unrelated_400_is_not_retried() -> None:
    respx.post(f"{BASE}/chat/completions").mock(
        return_value=httpx.Response(400, json={"error": {"message": "prompt is too long"}})
    )
    with pytest.raises(TouchstoneError):
        _compat().generate("m", "p", GenerationSettings())


@respx.mock
def test_model_list_accepts_plain_array() -> None:
    respx.get(f"{BASE}/models").mock(
        return_value=httpx.Response(200, json=[{"id": "z"}, {"id": "a"}])
    )
    assert _compat().list_models() == ["a", "z"]


def test_custom_server_needs_an_address() -> None:
    with pytest.raises(TouchstoneError, match="Custom server"):
        get_backend("custom")


@respx.mock
def test_custom_server_uses_saved_address_and_optional_key() -> None:
    save_custom_server("http://localhost:1234/v1/")
    route = respx.post("http://localhost:1234/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    )
    backend = get_backend("custom", max_attempts=1)
    assert backend.generate("my-model", "p", GenerationSettings()).text == "ok"
    assert "Authorization" not in route.calls.last.request.headers
    save_custom_server("https://api.example.test/v1", "my_secret_key_123")
    assert get_backend("custom").base_url == "https://api.example.test/v1"


@pytest.mark.parametrize("bad", ["", "ftp://x.test", "not a url", "localhost:1234", "https://"])
def test_custom_server_rejects_bad_address(bad: str) -> None:
    with pytest.raises(ValueError):
        save_custom_server(bad)
