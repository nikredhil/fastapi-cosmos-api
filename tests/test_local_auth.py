"""Local email/password account flow: register, login, and use the token."""
from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest_asyncio.fixture
async def real_client():
    """Client with the REAL auth validator (no override), so locally minted
    HS256 tokens are validated end to end."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with app.router.lifespan_context(app):
            yield ac


async def test_register_login_and_access(real_client: AsyncClient) -> None:
    # Register a new account → get a token back.
    resp = await real_client.post(
        "/auth/register",
        json={"email": "Sam@Example.com", "password": "hunter2pass", "display_name": "Sam"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["display_name"] == "Sam"
    token = body["access_token"]

    # The local token is accepted on a protected route.
    me = await real_client.get("/projects", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200

    # Email is normalized → duplicate registration is rejected.
    dup = await real_client.post(
        "/auth/register", json={"email": "sam@example.com", "password": "anotherpass"}
    )
    assert dup.status_code == 409

    # Login with correct credentials works; wrong password is 401.
    ok = await real_client.post(
        "/auth/login", json={"email": "sam@example.com", "password": "hunter2pass"}
    )
    assert ok.status_code == 200
    bad = await real_client.post(
        "/auth/login", json={"email": "sam@example.com", "password": "nope"}
    )
    assert bad.status_code == 401


async def test_login_unknown_user(real_client: AsyncClient) -> None:
    resp = await real_client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "whatever1"}
    )
    assert resp.status_code == 401


async def test_register_rejects_bad_email(real_client: AsyncClient) -> None:
    resp = await real_client.post(
        "/auth/register", json={"email": "not-an-email", "password": "longenough1"}
    )
    assert resp.status_code == 422


async def test_local_user_data_is_isolated(real_client: AsyncClient) -> None:
    # Two accounts can't see each other's projects (owner = local:<email>).
    t1 = (
        await real_client.post(
            "/auth/register", json={"email": "a@example.com", "password": "password1"}
        )
    ).json()["access_token"]
    t2 = (
        await real_client.post(
            "/auth/register", json={"email": "b@example.com", "password": "password2"}
        )
    ).json()["access_token"]

    await real_client.post(
        "/projects", json={"name": "A's project"}, headers={"Authorization": f"Bearer {t1}"}
    )
    listing = await real_client.get("/projects", headers={"Authorization": f"Bearer {t2}"})
    assert listing.json()["count"] == 0
