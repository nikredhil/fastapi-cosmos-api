"""In-process rate limiting for sensitive endpoints (e.g. login).

A sliding-window counter keyed by client IP + a discriminator (the email being
attempted). No external store: the WiseRent backend runs as a single instance
on Render, so an in-memory window is enough to blunt password brute-forcing.
Counts reset on restart, which is acceptable for this purpose. For a multi-
instance deployment, swap this for a shared store (e.g. Redis).
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class SlidingWindowLimiter:
    """Allow at most ``max_attempts`` hits per ``window_seconds`` for each key."""

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self._max = max_attempts
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str) -> tuple[bool, int]:
        """Record an attempt for ``key``.

        Returns ``(allowed, retry_after_seconds)``. When the window is full the
        attempt is *not* recorded and ``allowed`` is False with the number of
        seconds until the oldest hit ages out.
        """
        now = time.monotonic()
        cutoff = now - self._window
        bucket = self._hits[key]
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= self._max:
            retry_after = int(bucket[0] + self._window - now) + 1
            return False, max(retry_after, 1)
        bucket.append(now)
        return True, 0


def client_ip(request: Request) -> str:
    """Best-effort client IP, honouring Render's ``X-Forwarded-For`` proxy header."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_login_limit(request: Request, email: str) -> None:
    """Raise 429 if the (IP, email) pair has exceeded the configured login limit.

    No-op when the app has no limiter on ``state`` (e.g. some test setups).
    """
    limiter: SlidingWindowLimiter | None = getattr(request.app.state, "login_limiter", None)
    if limiter is None:
        return
    key = f"{client_ip(request)}:{email.strip().lower()}"
    allowed, retry_after = limiter.hit(key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please wait a moment and try again.",
            headers={"Retry-After": str(retry_after)},
        )
