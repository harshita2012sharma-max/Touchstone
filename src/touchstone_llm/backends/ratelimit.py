"""Client-side rate limiting and retries for free-tier APIs.

Free tiers allow only a few requests per minute. We space requests out
ourselves and retry politely when the provider still says "slow down".
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from touchstone_llm.backends.errors import RateLimitError, TransientError

T = TypeVar("T")

MAX_WAIT_SECONDS = 120.0
"""Longer waits usually mean a daily quota is used up; we stop instead of hanging."""


class RateLimiter:
    """Keep at least ``60 / requests_per_minute`` seconds between requests.

    ``requests_per_minute=None`` disables limiting (used for local Ollama).
    """

    def __init__(
        self,
        requests_per_minute: float | None,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create a limiter; ``clock`` and ``sleep`` are injectable for tests."""
        if requests_per_minute is not None and requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive or None")
        self._interval = 60.0 / requests_per_minute if requests_per_minute else 0.0
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None

    def acquire(self) -> None:
        """Block until the next request is allowed."""
        if not self._interval:
            return
        now = self._clock()
        if self._last is not None:
            wait = self._last + self._interval - now
            if wait > 0:
                self._sleep(wait)
                now = self._clock()
        self._last = now


def with_retries(
    fn: Callable[[], T],
    *,
    max_attempts: int,
    base_delay: float,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``fn``; retry on rate limits and transient errors with exponential backoff.

    Uses the provider's ``Retry-After`` when given. Raises the last error after
    ``max_attempts`` tries, or at once if the provider asks for a wait longer
    than ``MAX_WAIT_SECONDS``. Other exceptions are never retried.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except (RateLimitError, TransientError) as err:
            if attempt == max_attempts:
                raise
            retry_after = err.retry_after if isinstance(err, RateLimitError) else None
            if retry_after is not None and retry_after > MAX_WAIT_SECONDS:
                raise
            delay = retry_after or min(base_delay * 2 ** (attempt - 1), MAX_WAIT_SECONDS)
            sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover
