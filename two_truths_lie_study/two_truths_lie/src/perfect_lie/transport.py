"""Transport-level retry for live calls (brief §8 item 30).

Only failures where no answer came back are retried: rate limits (HTTP 429), timeouts and dropped
connections. They say nothing about the content of the call. A malformed or filtered answer is not
a transport failure and is left to the runner's existing parse handling, unchanged.
"""

from __future__ import annotations

import asyncio
import random
import re
from typing import Optional

TRANSPORT_PATTERN = re.compile(
    r"RateLimitError|Error code: 429|APITimeoutError|Request timed out|APIConnectionError|Connection error"
    # Pre-data change for the reversed-note follow-up (owner, 2026-10-10): EDSL's own timeout wording.
    # Only the timeout form of LanguageModelNoResponseError, not every no-response error.
    r"|LanguageModelNoResponseError: Language model timed out",
    re.IGNORECASE)
BACKOFF_SECONDS = (5, 15, 45, 90, 180)


def is_transport_error(err) -> bool:
    """True for a failure that returned no answer for network or provider reasons."""
    return bool(TRANSPORT_PATTERN.search(str(err) if not isinstance(err, BaseException)
                                         else f"{type(err).__name__}: {err}"))


def failed_by_transport(record: dict) -> bool:
    """A failed cell whose last error was a transport failure (retryable under item 30)."""
    errs = record.get("errors") or []
    return record.get("status") == "error" and bool(errs) and is_transport_error(errs[-1].get("error", ""))


class TransportRetryAdapter:
    """Wraps an adapter; retries acall/achat with backoff on transport errors only."""

    def __init__(self, inner, backoff=BACKOFF_SECONDS, sleep=asyncio.sleep, jitter: float = 0.25):
        self.inner = inner
        self.backoff = tuple(backoff)
        self._sleep = sleep
        self._jitter = jitter
        self.retries = 0

    def __getattr__(self, name):
        return getattr(self.inner, name)

    async def _with_retry(self, fn, *args, **kwargs):
        for i in range(len(self.backoff) + 1):
            try:
                return await fn(*args, **kwargs)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if i == len(self.backoff) or not is_transport_error(e):
                    raise
                self.retries += 1
                delay = self.backoff[i] * (1 + self._jitter * random.random())
                await self._sleep(delay)

    async def acall(self, *args, **kwargs):
        return await self._with_retry(self.inner.acall, *args, **kwargs)

    async def achat(self, *args, **kwargs):
        return await self._with_retry(self.inner.achat, *args, **kwargs)
