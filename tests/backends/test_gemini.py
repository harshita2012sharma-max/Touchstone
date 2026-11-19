import json

import httpx
import pytest
import respx

from touchstone_llm.backends.base import AuthError, ModelNotFoundError
from touchstone_llm.backends.gemini import GEMINI_BASE_URL, GeminiBackend
from touchstone_llm.config import GenerationSettings

KEY = "AIza_test_secret_value_123"


def _backend() -> GeminiBackend:
    return GeminiBackend(api_key=KEY, requests_per_minute=None, max_attempts=1)


@respx.mock
def test_generate_payload_and_key_in_header_not_url() -> None:
    route = respx.post(f"{GEMINI_BASE_URL}/models/fake-gemini:generateContent").mock(
        return_value=httpx.Response(
            200,
            json={
                "modelVersion": "fake-gemini-001",
                "candidates": [
                    {
                        "content": {"parts": [{"text": "उत्तर: "}, {"text": "C"}]},
                        "finishReason": "STOP",
                    }
                ],
            },
        )
    )
    out = _backend().generate("fake-gemini", "प्रश्न", GenerationSettings())
    assert out.text == "उत्तर: C"
    assert out.model_id == "fake-gemini-001"
    assert out.finish_reason == "STOP"

    request = route.calls.last.request
    assert request.headers["x-goog-api-key"] == KEY
    assert KEY not in str(request.url)
    body = json.loads(request.content)
    assert body["contents"] == [{"role": "user", "parts": [{"text": "प्रश्न"}]}]
    assert body["generationConfig"] == {
        "temperature": 0.0,
        "topP": 1.0,
        "maxOutputTokens": 512,
        "seed": 42,
    }


@respx.mock
def test_blocked_reply_returns_empty_text_with_reason() -> None:
    respx.post(f"{GEMINI_BASE_URL}/models/m:generateContent").mock(
        return_value=httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})
    )
    out = _backend().generate("m", "p", GenerationSettings())
    assert out.text == ""
    assert out.finish_reason == "SAFETY"


@respx.mock
def test_model_id_with_models_prefix_is_accepted() -> None:
    route = respx.post(f"{GEMINI_BASE_URL}/models/m:generateContent").mock(
        return_value=httpx.Response(200, json={"candidates": []})
    )
    _backend().generate("models/m", "p", GenerationSettings())
    assert route.called


@respx.mock
def test_404_suggests_list_models() -> None:
    respx.post(f"{GEMINI_BASE_URL}/models/old:generateContent").mock(
        return_value=httpx.Response(404, json={"error": {"message": "models/old is not found"}})
    )
    with pytest.raises(ModelNotFoundError, match="touchstone list-models gemini"):
        _backend().generate("old", "p", GenerationSettings())


@respx.mock
def test_invalid_key_is_auth_error() -> None:
    respx.post(f"{GEMINI_BASE_URL}/models/m:generateContent").mock(
        return_value=httpx.Response(
            400,
            json={
                "error": {
                    "message": "API key not valid.",
                    "status": "INVALID_ARGUMENT",
                    "details": [{"reason": "API_KEY_INVALID"}],
                }
            },
        )
    )
    with pytest.raises(AuthError):
        _backend().generate("m", "p", GenerationSettings())


@respx.mock
def test_list_models_paginates_and_filters() -> None:
    respx.get(f"{GEMINI_BASE_URL}/models").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "name": "models/b-chat",
                            "supportedGenerationMethods": ["generateContent"],
                        },
                        {"name": "models/embed", "supportedGenerationMethods": ["embedContent"]},
                    ],
                    "nextPageToken": "page2",
                },
            ),
            httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "models/a-chat", "supportedGenerationMethods": ["generateContent"]}
                    ]
                },
            ),
        ]
    )
    assert _backend().list_models() == ["a-chat", "b-chat"]
