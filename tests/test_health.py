"""Health and auth endpoint tests."""
from __future__ import annotations

from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db_backend"] == "memory"


async def test_protected_route_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/projects")
    assert resp.status_code == 403  # no bearer credentials supplied


async def test_token_then_access(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.get("/projects", headers=auth_headers)
    assert resp.status_code == 200
