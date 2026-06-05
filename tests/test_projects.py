"""Project and task CRUD flow tests against the in-memory backend."""
from __future__ import annotations

from httpx import AsyncClient


async def test_project_crud(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # Create
    resp = await client.post(
        "/projects", json={"name": "Website redesign"}, headers=auth_headers
    )
    assert resp.status_code == 201
    project = resp.json()
    pid = project["id"]
    assert project["name"] == "Website redesign"
    assert project["owner"] == "alice"

    # Read
    resp = await client.get(f"/projects/{pid}", headers=auth_headers)
    assert resp.status_code == 200

    # Update
    resp = await client.patch(
        f"/projects/{pid}", json={"description": "Q3 initiative"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Q3 initiative"

    # List
    resp = await client.get("/projects", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["count"] == 1

    # Delete
    resp = await client.delete(f"/projects/{pid}", headers=auth_headers)
    assert resp.status_code == 204
    resp = await client.get(f"/projects/{pid}", headers=auth_headers)
    assert resp.status_code == 404


async def test_task_flow_and_isolation(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    pid = (
        await client.post("/projects", json={"name": "Backend"}, headers=auth_headers)
    ).json()["id"]

    # Create a task under the project
    resp = await client.post(
        f"/projects/{pid}/tasks",
        json={"title": "Write tests", "priority": "high"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    task = resp.json()
    assert task["status"] == "todo"
    assert task["priority"] == "high"

    # Filter by status
    resp = await client.get(
        f"/projects/{pid}/tasks", params={"status": "todo"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 1

    resp = await client.get(
        f"/projects/{pid}/tasks", params={"status": "done"}, headers=auth_headers
    )
    assert resp.json()["count"] == 0


def _headers_for(username: str) -> dict[str, str]:
    # The test auth override (conftest) treats the Bearer value as the user id.
    return {"Authorization": f"Bearer {username}"}


async def test_cannot_access_other_users_project(client: AsyncClient) -> None:
    alice = _headers_for("alice")
    bob = _headers_for("bob")

    # Alice creates a project; the partition key is her user subject.
    pid = (
        await client.post("/projects", json={"name": "Secret"}, headers=alice)
    ).json()["id"]

    # Bob cannot read it and sees none in his own listing.
    assert (await client.get(f"/projects/{pid}", headers=bob)).status_code == 404
    assert (await client.get("/projects", headers=bob)).json()["count"] == 0
