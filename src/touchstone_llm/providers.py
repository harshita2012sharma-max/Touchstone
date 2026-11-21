"""The provider catalog: every model service touchstone can talk to.

One list drives the CLI, the API-key handling and the web UI. Each user brings
their own key for whichever provider they choose; keys are never shipped.

``verified`` marks providers that have been run end to end against the real
service by the maintainers. The others use the same, standard request format
and are covered by tests, but are labelled beta until someone confirms them.
Default request rates are cautious; providers change limits, so ``--rpm``
overrides them.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from typing import Literal

Kind = Literal["openai", "gemini", "anthropic", "ollama", "mock", "custom"]
Group = Literal["free", "paid", "local", "own"]


@dataclass(frozen=True)
class ProviderInfo:
    """Everything touchstone needs to know about one provider."""

    name: str
    label: str
    description: str
    kind: Kind
    group: Group
    base_url: str | None = None
    env_var: str | None = None
    signup_url: str | None = None
    rpm: float | None = 30.0
    verified: bool = False
    # Glob patterns, best first, matched against the provider's live model list
    # to suggest good chat models. Patterns (not fixed ids) so that new versions
    # still match and retired ones simply drop out.
    recommended: tuple[str, ...] = ()
    # Shown as the placeholder when typing a model name by hand.
    example_model: str = ""


CATALOG: tuple[ProviderInfo, ...] = (
    ProviderInfo(
        "gemini",
        "Google Gemini",
        "Google's Gemini models. Free key, generous limits.",
        "gemini",
        "free",
        env_var="GEMINI_API_KEY",
        signup_url="https://aistudio.google.com/apikey",
        rpm=10,
        verified=True,
        recommended=("gemini-*-flash", "gemini-*-flash-lite", "gemini-*-pro", "gemini-*flash*"),
        example_model="gemini-2.5-flash",
    ),
    ProviderInfo(
        "groq",
        "Groq",
        "Very fast open models such as Llama, Qwen and GPT-OSS. Free key.",
        "openai",
        "free",
        base_url="https://api.groq.com/openai/v1",
        env_var="GROQ_API_KEY",
        signup_url="https://console.groq.com/keys",
        rpm=30,
        verified=True,
        recommended=(
            "llama-3.3-70b-versatile",
            "openai/gpt-oss-*",
            "qwen/*",
            "meta-llama/llama-4-*",
            "llama-*",
        ),
        example_model="llama-3.3-70b-versatile",
    ),
    ProviderInfo(
        "openrouter",
        "OpenRouter",
        "Hundreds of models from many companies with one key.",
        "openai",
        "free",
        base_url="https://openrouter.ai/api/v1",
        env_var="OPENROUTER_API_KEY",
        signup_url="https://openrouter.ai/keys",
        rpm=20,
        verified=True,
        recommended=(
            "google/gemma-*:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/*:free",
            "qwen/*:free",
            "mistralai/*:free",
            "*:free",
        ),
        example_model="meta-llama/llama-3.3-70b-instruct:free",
    ),
    ProviderInfo(
        "huggingface",
        "Hugging Face",
        "Open models through Hugging Face's inference router.",
        "openai",
        "free",
        base_url="https://router.huggingface.co/v1",
        env_var="HF_TOKEN",
        signup_url="https://huggingface.co/settings/tokens",
        rpm=20,
        recommended=(
            "meta-llama/Llama-3.3-70B-Instruct*",
            "Qwen/Qwen*-Instruct*",
            "google/gemma-*-it",
            "deepseek-ai/DeepSeek-V3*",
            "openai/gpt-oss-*",
        ),
        example_model="meta-llama/Llama-3.3-70B-Instruct",
    ),
    ProviderInfo(
        "openai",
        "OpenAI",
        "GPT models from OpenAI. Paid API key.",
        "openai",
        "paid",
        base_url="https://api.openai.com/v1",
        env_var="OPENAI_API_KEY",
        signup_url="https://platform.openai.com/api-keys",
        rpm=60,
        recommended=("gpt-5*-mini", "gpt-4.1-mini", "gpt-4o-mini", "gpt-5*", "gpt-4.1", "gpt-4o"),
        example_model="gpt-4o-mini",
    ),
    ProviderInfo(
        "anthropic",
        "Anthropic",
        "Claude models from Anthropic. Paid API key.",
        "anthropic",
        "paid",
        base_url="https://api.anthropic.com/v1",
        env_var="ANTHROPIC_API_KEY",
        signup_url="https://console.anthropic.com/",
        rpm=50,
        recommended=("claude-haiku-*", "claude-sonnet-*", "claude-opus-*", "claude-3-5-haiku-*"),
        example_model="claude-haiku-4-5",
    ),
    ProviderInfo(
        "mistral",
        "Mistral",
        "Mistral's own models. Paid API key (free trial tier available).",
        "openai",
        "paid",
        base_url="https://api.mistral.ai/v1",
        env_var="MISTRAL_API_KEY",
        signup_url="https://console.mistral.ai/api-keys",
        rpm=30,
        recommended=(
            "mistral-small-latest",
            "mistral-large-latest",
            "mistral-medium-latest",
            "open-mistral-nemo",
        ),
        example_model="mistral-small-latest",
    ),
    ProviderInfo(
        "deepseek",
        "DeepSeek",
        "DeepSeek chat and reasoning models. Paid API key.",
        "openai",
        "paid",
        base_url="https://api.deepseek.com/v1",
        env_var="DEEPSEEK_API_KEY",
        signup_url="https://platform.deepseek.com/api_keys",
        rpm=30,
        recommended=("deepseek-chat", "deepseek-reasoner"),
        example_model="deepseek-chat",
    ),
    ProviderInfo(
        "xai",
        "xAI",
        "Grok models from xAI. Paid API key.",
        "openai",
        "paid",
        base_url="https://api.x.ai/v1",
        env_var="XAI_API_KEY",
        signup_url="https://console.x.ai/",
        rpm=30,
        recommended=("grok-*-mini*", "grok-*-fast*", "grok-4*", "grok-*"),
        example_model="grok-3-mini",
    ),
    ProviderInfo(
        "together",
        "Together AI",
        "Many open models on one paid API.",
        "openai",
        "paid",
        base_url="https://api.together.xyz/v1",
        env_var="TOGETHER_API_KEY",
        signup_url="https://api.together.ai/settings/api-keys",
        rpm=30,
        recommended=(
            "meta-llama/Llama-3.3-70B-Instruct-Turbo*",
            "Qwen/*Instruct*",
            "deepseek-ai/DeepSeek-V3*",
            "google/gemma-*",
        ),
        example_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    ),
    ProviderInfo(
        "ollama",
        "Ollama (this computer)",
        "Runs a model on this computer. No key, works offline.",
        "ollama",
        "local",
        rpm=None,
        verified=True,
        recommended=("llama3*", "qwen*", "gemma*", "mistral*", "*"),
        example_model="llama3.2",
    ),
    ProviderInfo(
        "custom",
        "Custom server",
        "Any OpenAI-compatible address: your company, LM Studio, vLLM, or another provider.",
        "custom",
        "own",
        rpm=30,
        recommended=("*",),
        example_model="your-model-name",
    ),
    ProviderInfo(
        "mock",
        "Practice (mock)",
        'A pretend model for practice. Always answers "A". No key.',
        "mock",
        "local",
        rpm=None,
        verified=True,
        recommended=("fixed", "echo"),
        example_model="fixed",
    ),
)

BY_NAME: dict[str, ProviderInfo] = {p.name: p for p in CATALOG}

CUSTOM_URL_VAR = "CUSTOM_BASE_URL"
CUSTOM_KEY_VAR = "CUSTOM_API_KEY"

# Words in model ids that mark models which cannot answer chat questions.
_NOT_CHAT = (
    "embed",
    "whisper",
    "tts",
    "dall-e",
    "moderation",
    "guard",
    "transcribe",
    "realtime",
    "audio",
    "image",
    "rerank",
    "vision-preview",
)


def recommend(provider: str, models: list[str], limit: int = 5) -> list[str]:
    """Pick up to ``limit`` suggested models from a provider's live ``models`` list.

    Follows the provider's ``recommended`` patterns in order. Within one pattern
    ids are sorted newest-looking first (reverse order puts higher version
    numbers first). Named families take turns (best of each, then second best
    of each), so the suggestions cover different families; catch-all patterns
    that start with ``*`` only fill the places left over. Only ids that really
    exist in ``models`` are returned.
    """
    info = BY_NAME.get(provider)
    if info is None:
        return []
    chat = [m for m in models if not any(word in m.lower() for word in _NOT_CHAT)]

    def matches(pattern: str) -> list[str]:
        return sorted((m for m in chat if fnmatchcase(m, pattern)), reverse=True)

    named = [matches(p) for p in info.recommended if not p.startswith("*")]
    fallback = [m for p in info.recommended if p.startswith("*") for m in matches(p)]
    ordered = [
        g[rank] for rank in range(max(map(len, named), default=0)) for g in named if rank < len(g)
    ]
    picked: list[str] = []
    for model in ordered + fallback:
        if model not in picked:
            picked.append(model)
            if len(picked) >= limit:
                break
    return picked
