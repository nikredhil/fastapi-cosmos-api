"""Shared test fixtures."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest_asyncio.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # The lifespan must run so app.state services are wired up.
        async with app.router.lifespan_context(app):
            yield ac


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    resp = await client.post("/auth/token", json={"username": "alice"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
