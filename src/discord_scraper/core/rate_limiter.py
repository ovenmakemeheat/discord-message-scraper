from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

import httpx


@dataclass
class RateLimitStats:
    hits: int = 0
    total_wait: float = 0.0


class RateLimiter:
    """Handles Discord API rate limiting with retry and backoff."""

    def __init__(self, max_retries: int = 5) -> None:
        self._max_retries = max_retries
        self.stats = RateLimitStats()

    def execute(self, request_fn: Callable[[], httpx.Response]) -> httpx.Response:
        for attempt in range(self._max_retries):
            response = request_fn()
            if response.status_code != 429:
                return response

            retry_after = self._parse_retry_after(response)
            wait = retry_after + 0.5
            self.stats.hits += 1
            self.stats.total_wait += wait
            time.sleep(wait)

        return request_fn()

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> float:
        try:
            return float(response.json().get("retry_after", 5))
        except Exception:
            return float(response.headers.get("Retry-After", "5"))
