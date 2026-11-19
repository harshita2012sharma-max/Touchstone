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
    ),
    ProviderInfo(
        "ollama",
        "Ollama (this computer)",
        "Runs a model on this computer. No key, works offline.",
        "ollama",
        "local",
        rpm=None,
        verified=True,
    ),
    ProviderInfo(
        "custom",
        "Custom server",
        "Any OpenAI-compatible address: your company, LM Studio, vLLM, or another provider.",
        "custom",
        "own",
        rpm=30,
    ),
    ProviderInfo(
        "mock",
        "Practice (mock)",
        'A pretend model for practice. Always answers "A". No key.',
        "mock",
        "local",
        rpm=None,
        verified=True,
    ),
)

BY_NAME: dict[str, ProviderInfo] = {p.name: p for p in CATALOG}

CUSTOM_URL_VAR = "CUSTOM_BASE_URL"
CUSTOM_KEY_VAR = "CUSTOM_API_KEY"
