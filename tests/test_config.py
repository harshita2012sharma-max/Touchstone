import pytest
from pydantic import ValidationError

from kasauti.config import GenerationSettings, ModelRef, RunConfig


def test_model_ref_splits_on_first_slash_only() -> None:
    ref = ModelRef.parse("openrouter/some-org/some-model:free")
    assert ref.provider == "openrouter"
    assert ref.model_id == "some-org/some-model:free"
    assert str(ref) == "openrouter/some-org/some-model:free"


def test_model_ref_lowercases_provider() -> None:
    assert ModelRef.parse("Groq/fake-model").provider == "groq"


@pytest.mark.parametrize("bad", ["", "groq", "groq/", "/model", "  /  "])
def test_model_ref_rejects_bad_strings(bad: str) -> None:
    with pytest.raises(ValueError, match="provider/model"):
        ModelRef.parse(bad)


def test_generation_defaults_are_deterministic() -> None:
    settings = GenerationSettings()
    assert settings.temperature == 0.0
    assert settings.seed == 42
    assert settings.top_p == 1.0
    assert settings.max_tokens == 512


@pytest.mark.parametrize(
    "field,value",
    [("temperature", -0.1), ("temperature", 2.1), ("max_tokens", 0), ("top_p", 1.5)],
)
def test_generation_rejects_out_of_range(field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        GenerationSettings(**{field: value})


def test_run_config_parses_model_and_dedupes_tasks() -> None:
    cfg = RunConfig(model="mock/fake", tasks=["a", "b", "a"])
    assert cfg.model_ref.provider == "mock"
    assert cfg.tasks == ["a", "b"]
    assert cfg.limit is None


def test_run_config_requires_tasks() -> None:
    with pytest.raises(ValidationError):
        RunConfig(model="mock/fake", tasks=[])


def test_run_config_rejects_bad_model() -> None:
    with pytest.raises(ValidationError, match="provider/model"):
        RunConfig(model="no-slash", tasks=["a"])


def test_run_config_limit_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        RunConfig(model="mock/fake", tasks=["a"], limit=0)
