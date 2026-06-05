"""Health and auth endpoint tests."""
from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest_asyncio.fixture
async def raw_client():
    """A client WITHOUT the auth override, so the real Microsoft token validator runs.

    Azure config is injected so requests get past the 'not configured' guard and
    exercise actual token validation.
    """
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        azure_client_id="test-client-id", db_backend="memory"
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with app.router.lifespan_context(app):
            yield ac
    app.dependency_overrides.clear()


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db_backend"] == "memory"


async def test_protected_route_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/buildings")
    assert resp.status_code == 403  # no bearer credentials supplied


async def test_token_then_access(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.get("/buildings", headers=auth_headers)
    assert resp.status_code == 200


async def test_auth_config_exposes_client_id(raw_client: AsyncClient) -> None:
    resp = await raw_client.get("/auth/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["client_id"] == "test-client-id"
    assert "login.microsoftonline.com" in body["authority"]


async def test_garbage_token_rejected(raw_client: AsyncClient) -> None:
    # A malformed bearer is rejected by the real validator without any network call.
    resp = await raw_client.get("/buildings", headers={"Authorization": "Bearer not.a.jwt"})
    assert resp.status_code == 401
