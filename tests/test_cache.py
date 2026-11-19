from pathlib import Path

from touchstone_llm.backends.base import Completion
from touchstone_llm.cache import ResponseCache, cache_key
from touchstone_llm.config import GenerationSettings


def test_cache_round_trip(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "c.sqlite")
    key = cache_key("groq/m", "प्रश्न", GenerationSettings())
    assert cache.get(key) is None
    cache.put(key, Completion(text="उत्तर", model_id="m-1", latency_ms=5))
    again = ResponseCache(tmp_path / "c.sqlite")
    got = again.get(key)
    assert got is not None
    assert got.text == "उत्तर"
    assert got.model_id == "m-1"


def test_key_changes_with_inputs() -> None:
    s = GenerationSettings()
    base = cache_key("groq/m", "p", s)
    assert base == cache_key("groq/m", "p", s)
    assert base != cache_key("groq/other", "p", s)
    assert base != cache_key("groq/m", "p2", s)
    assert base != cache_key("groq/m", "p", GenerationSettings(max_tokens=100))
