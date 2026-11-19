import json

import httpx
import pytest
import respx

from kasauti.backends.base import (
    AuthError,
    BackendError,
    ModelNotFoundError,
    RateLimitError,
)
from kasauti.backends.openai_compat import OpenAICompatBackend
from kasauti.config import GenerationSettings

BASE = "https://api.example.test/v1"
KEY = "sk_test_secret_value_123"


def _backend(api_key: str | None = KEY, name: str = "groq") -> OpenAICompatBackend:
    return OpenAICompatBackend(
        name=name, base_url=BASE, api_key=api_key, requests_per_minute=None, max_attempts=1
    )


@respx.mock
def test_generate_sends_settings_and_parses_reply() -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "fake-model-2025",
                "choices": [{"message": {"content": "उत्तर: B"}, "finish_reason": "stop"}],
            },
        )
    )
    out = _backend().generate("fake-model", "प्रश्न", GenerationSettings())
    assert out.text == "उत्तर: B"
    assert out.model_id == "fake-model-2025"
    assert out.finish_reason == "stop"
    assert out.latency_ms >= 0

    request = route.calls.last.request
    assert request.headers["Authorization"] == f"Bearer {KEY}"
    body = json.loads(request.content)
    assert body == {
        "model": "fake-model",
        "messages": [{"role": "user", "content": "प्रश्न"}],
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 512,
        "seed": 42,
    }


@respx.mock
def test_no_auth_header_without_key() -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "x"}}]})
    )
    _backend(api_key=None, name="ollama").generate("m", "p", GenerationSettings())
    assert "Authorization" not in route.calls.last.request.headers


@respx.mock
def test_null_content_becomes_empty_string() -> None:
    respx.post(f"{BASE}/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": None}}]})
    )
    assert _backend().generate("m", "p", GenerationSettings()).text == ""


@pytest.mark.parametrize(
    "status,payload",
    [
        (404, {"error": {"message": "The model `old` does not exist", "code": "model_not_found"}}),
        (400, {"error": {"message": "The model `old` has been decommissioned"}}),
        (400, {"error": {"message": "old is not a valid model ID"}}),
    ],
)
@respx.mock
def test_retired_or_unknown_model_suggests_list_models(status: int, payload: dict) -> None:
    respx.post(f"{BASE}/chat/completions").mock(return_value=httpx.Response(status, json=payload))
    with pytest.raises(ModelNotFoundError) as exc:
        _backend().generate("old", "p", GenerationSettings())
    assert "kasauti list-models groq" in str(exc.value)


@respx.mock
def test_auth_error_never_contains_key() -> None:
    respx.post(f"{BASE}/chat/completions").mock(
        return_value=httpx.Response(401, json={"error": {"message": f"Invalid key {KEY}"}})
    )
    with pytest.raises(AuthError) as exc:
        _backend().generate("m", "p", GenerationSettings())
    assert KEY not in str(exc.value)
    assert "rejected" in str(exc.value)


@respx.mock
def test_429_raises_rate_limit_with_retry_after() -> None:
    respx.post(f"{BASE}/chat/completions").mock(
        return_value=httpx.Response(429, headers={"retry-after": "12"}, json={})
    )
    with pytest.raises(RateLimitError) as exc:
        _backend().generate("m", "p", GenerationSettings())
    assert exc.value.retry_after == 12.0


@respx.mock
def test_retries_server_errors_then_succeeds() -> None:
    respx.post(f"{BASE}/chat/completions").mock(
        side_effect=[
            httpx.Response(503, json={}),
            httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}),
        ]
    )
    backend = OpenAICompatBackend(
        name="groq",
        base_url=BASE,
        api_key=KEY,
        requests_per_minute=None,
        max_attempts=3,
        sleep=lambda _s: None,
    )
    assert backend.generate("m", "p", GenerationSettings()).text == "ok"


@respx.mock
def test_connection_error_has_helpful_hint() -> None:
    respx.post(f"{BASE}/chat/completions").mock(side_effect=httpx.ConnectError("refused"))
    backend = OpenAICompatBackend(
        name="ollama",
        base_url=BASE,
        api_key=None,
        requests_per_minute=None,
        max_attempts=1,
        connect_hint="Is Ollama running? Start it with `ollama serve`.",
    )
    with pytest.raises(BackendError, match="ollama serve"):
        backend.generate("m", "p", GenerationSettings())


@respx.mock
def test_list_models_sorted_ids() -> None:
    respx.get(f"{BASE}/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "zeta"}, {"id": "alpha"}]})
    )
    assert _backend().list_models() == ["alpha", "zeta"]
