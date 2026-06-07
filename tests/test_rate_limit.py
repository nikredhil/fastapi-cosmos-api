"""Tests for login brute-force rate limiting."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.core.rate_limit import SlidingWindowLimiter
from app.main import create_app


def test_sliding_window_allows_up_to_limit_then_blocks() -> None:
    limiter = SlidingWindowLimiter(max_attempts=3, window_seconds=60)
    assert [limiter.hit("k")[0] for _ in range(3)] == [True, True, True]
    allowed, retry_after = limiter.hit("k")
    assert allowed is False
    assert retry_after >= 1


def test_sliding_window_keys_are_independent() -> None:
    limiter = SlidingWindowLimiter(max_attempts=1, window_seconds=60)
    assert limiter.hit("a")[0] is True
    assert limiter.hit("a")[0] is False
    # A different key has its own budget.
    assert limiter.hit("b")[0] is True


@pytest_asyncio.fixture
async def low_limit_client():
    """App whose login limiter trips after 2 attempts, for fast assertions."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(db_backend="memory")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with app.router.lifespan_context(app):
            app.state.login_limiter = SlidingWindowLimiter(max_attempts=2, window_seconds=60)
            yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_returns_429_after_limit(low_limit_client: AsyncClient) -> None:
    body = {"email": "nobody@example.com", "password": "wrongpassword"}
    # First two attempts fail auth (401) but are allowed through.
    assert (await low_limit_client.post("/auth/login", json=body)).status_code == 401
    assert (await low_limit_client.post("/auth/login", json=body)).status_code == 401
    # Third is throttled before reaching the auth check.
    blocked = await low_limit_client.post("/auth/login", json=body)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
