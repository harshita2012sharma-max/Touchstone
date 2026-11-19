import pytest

from touchstone_llm.backends.base import RateLimitError, TransientError
from touchstone_llm.backends.ratelimit import RateLimiter, with_retries


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_rate_limiter_spaces_requests() -> None:
    clock = FakeClock()
    limiter = RateLimiter(requests_per_minute=30, clock=clock.time, sleep=clock.sleep)
    limiter.acquire()
    limiter.acquire()
    limiter.acquire()
    assert clock.sleeps == [pytest.approx(2.0), pytest.approx(2.0)]


def test_rate_limiter_does_not_sleep_when_enough_time_passed() -> None:
    clock = FakeClock()
    limiter = RateLimiter(requests_per_minute=60, clock=clock.time, sleep=clock.sleep)
    limiter.acquire()
    clock.now += 5
    limiter.acquire()
    assert clock.sleeps == []


def test_rate_limiter_none_means_unlimited() -> None:
    clock = FakeClock()
    limiter = RateLimiter(requests_per_minute=None, clock=clock.time, sleep=clock.sleep)
    for _ in range(5):
        limiter.acquire()
    assert clock.sleeps == []


def test_with_retries_retries_then_succeeds() -> None:
    clock = FakeClock()
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientError("503")
        return "ok"

    assert with_retries(flaky, max_attempts=5, base_delay=1.0, sleep=clock.sleep) == "ok"
    assert clock.sleeps == [1.0, 2.0]


def test_with_retries_honours_retry_after() -> None:
    clock = FakeClock()
    calls = {"n": 0}

    def limited() -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RateLimitError("429", retry_after=7.5)
        return "ok"

    with_retries(limited, max_attempts=3, base_delay=1.0, sleep=clock.sleep)
    assert clock.sleeps == [7.5]


def test_with_retries_gives_up() -> None:
    clock = FakeClock()

    def always_fails() -> str:
        raise TransientError("boom")

    with pytest.raises(TransientError):
        with_retries(always_fails, max_attempts=3, base_delay=1.0, sleep=clock.sleep)
    assert len(clock.sleeps) == 2


def test_with_retries_does_not_retry_other_errors() -> None:
    clock = FakeClock()

    def bad() -> str:
        raise ValueError("not retryable")

    with pytest.raises(ValueError):
        with_retries(bad, max_attempts=3, base_delay=1.0, sleep=clock.sleep)
    assert clock.sleeps == []
