"""Shared test fixtures."""
from __future__ import annotations

import os

# Force the in-memory backend for the whole test session before the app (and its
# cached settings) are imported, so tests never read/write the on-disk JSON store.
os.environ["DB_BACKEND"] = "memory"

import pytest_asyncio
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.core.security import get_current_user
from app.main import create_app

_bearer = HTTPBearer(auto_error=True)


def memory_settings() -> Settings:
    """Force the in-memory backend so tests never touch disk."""
    return Settings(db_backend="memory")


def _test_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """Test stand-in for Microsoft token validation.

    Real Entra ID tokens can't be minted in unit tests, so we treat the Bearer
    value itself as the user id (e.g. ``Authorization: Bearer alice`` → "alice").
    Applied via dependency override so the production validator is untouched.
    """
    return credentials.credentials


@pytest_asyncio.fixture
async def client():
    app = create_app()
    app.dependency_overrides[get_current_user] = _test_user
    app.dependency_overrides[get_settings] = memory_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # The lifespan must run so app.state services are wired up.
        async with app.router.lifespan_context(app):
            yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer alice"}
