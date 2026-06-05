"""Tests for members, sprints, item keys, points, comments, and filtering."""
from __future__ import annotations

from httpx import AsyncClient


async def _make_project(client: AsyncClient, headers: dict[str, str], name: str = "Web App") -> str:
    return (await client.post("/projects", json={"name": name}, headers=headers)).json()["id"]


async def test_member_crud_and_assignment(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    pid = await _make_project(client, auth_headers, "Website Migration")

    # Create a member.
    member = (
        await client.post(
            f"/projects/{pid}/members",
            json={"name": "Alice Chen", "role": "Designer"},
            headers=auth_headers,
        )
    ).json()
    assert member["name"] == "Alice Chen"
    assert member["avatar_color"]  # auto-assigned from palette

    # Listing returns the member.
    listing = (await client.get(f"/projects/{pid}/members", headers=auth_headers)).json()
    assert listing["count"] == 1

    # Assign a task to the member → assignee_name is denormalized server-side.
    task = (
        await client.post(
            f"/projects/{pid}/tasks",
            json={"title": "Build nav", "assignee_id": member["id"], "points": 5},
            headers=auth_headers,
        )
    ).json()
    assert task["assignee_id"] == member["id"]
    assert task["assignee_name"] == "Alice Chen"
    assert task["points"] == 5

    # Filter tasks by assignee.
    filtered = (
        await client.get(
            f"/projects/{pid}/tasks",
            params={"assignee_id": member["id"]},
            headers=auth_headers,
        )
    ).json()
    assert filtered["count"] == 1


async def test_item_key_and_type(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    pid = await _make_project(client, auth_headers, "Website Migration")  # prefix "WM"

    t1 = (
        await client.post(
            f"/projects/{pid}/tasks",
            json={"title": "First", "item_type": "bug"},
            headers=auth_headers,
        )
    ).json()
    t2 = (
        await client.post(
            f"/projects/{pid}/tasks", json={"title": "Second"}, headers=auth_headers
        )
    ).json()

    assert t1["key"] == "WM-1"
    assert t1["item_type"] == "bug"
    assert t2["key"] == "WM-2"


async def test_sprint_flow_and_backlog_filter(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    pid = await _make_project(client, auth_headers)

    sprint = (
        await client.post(
            f"/projects/{pid}/sprints",
            json={"name": "Sprint 1", "start_date": "2026-06-01", "end_date": "2026-06-14"},
            headers=auth_headers,
        )
    ).json()
    assert sprint["status"] == "planned"

    # Activate the sprint.
    activated = (
        await client.patch(
            f"/projects/{pid}/sprints/{sprint['id']}",
            json={"status": "active"},
            headers=auth_headers,
        )
    ).json()
    assert activated["status"] == "active"

    # One task in the sprint, one in the backlog.
    await client.post(
        f"/projects/{pid}/tasks",
        json={"title": "In sprint", "sprint_id": sprint["id"]},
        headers=auth_headers,
    )
    await client.post(
        f"/projects/{pid}/tasks", json={"title": "In backlog"}, headers=auth_headers
    )

    in_sprint = (
        await client.get(
            f"/projects/{pid}/tasks", params={"sprint_id": sprint["id"]}, headers=auth_headers
        )
    ).json()
    assert [t["title"] for t in in_sprint["items"]] == ["In sprint"]

    backlog = (
        await client.get(
            f"/projects/{pid}/tasks", params={"sprint_id": "backlog"}, headers=auth_headers
        )
    ).json()
    assert [t["title"] for t in backlog["items"]] == ["In backlog"]


async def test_comments(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    pid = await _make_project(client, auth_headers)
    tid = (
        await client.post(
            f"/projects/{pid}/tasks", json={"title": "Discuss"}, headers=auth_headers
        )
    ).json()["id"]

    updated = (
        await client.post(
            f"/projects/{pid}/tasks/{tid}/comments",
            json={"body": "Looks good to me"},
            headers=auth_headers,
        )
    ).json()
    assert len(updated["comments"]) == 1
    assert updated["comments"][0]["body"] == "Looks good to me"
    assert updated["comments"][0]["author"] == "alice"
