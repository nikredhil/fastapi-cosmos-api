"""Unit tests for the rule-based chat engine using an in-memory fake client."""
from __future__ import annotations

import uuid
from typing import Any

from app.chat.chat_engine import handle


class FakeClient:
    """Mimics ui.api_client.ApiClient with plain dicts — no network."""

    def __init__(self) -> None:
        self.projects: dict[str, dict[str, Any]] = {}
        self.tasks: dict[str, dict[str, Any]] = {}

    def list_projects(self) -> list[dict[str, Any]]:
        return list(self.projects.values())

    def create_project(self, name: str, description: str | None = None) -> dict[str, Any]:
        pid = str(uuid.uuid4())
        project = {"id": pid, "name": name, "description": description}
        self.projects[pid] = project
        return project

    def list_tasks(self, project_id: str, status: str | None = None) -> list[dict[str, Any]]:
        out = [t for t in self.tasks.values() if t["project_id"] == project_id]
        if status:
            out = [t for t in out if t["status"] == status]
        return out

    def create_task(self, project_id: str, title: str, **kwargs: Any) -> dict[str, Any]:
        tid = str(uuid.uuid4())
        task = {
            "id": tid,
            "project_id": project_id,
            "title": title,
            "status": kwargs.get("status", "todo"),
            "priority": kwargs.get("priority", "medium"),
            "assignee": kwargs.get("assignee"),
        }
        self.tasks[tid] = task
        return task


def test_help_and_greeting() -> None:
    client = FakeClient()
    assert "manage projects" in handle(client, "help")
    assert "assistant" in handle(client, "hello").lower()


def test_create_project_then_list() -> None:
    client = FakeClient()
    reply = handle(client, "create project Website Redesign")
    assert "Website Redesign" in reply
    assert len(client.projects) == 1

    listing = handle(client, "list my projects")
    assert "Website Redesign" in listing


def test_create_task_with_priority() -> None:
    client = FakeClient()
    handle(client, "create project Backend")
    reply = handle(client, "add task Write docs to Backend (priority high)")
    assert "Write docs" in reply
    task = next(iter(client.tasks.values()))
    assert task["title"] == "Write docs"
    assert task["priority"] == "high"


def test_create_task_natural_phrasing() -> None:
    client = FakeClient()
    client.create_project("Q3 Marketing Campaign")
    reply = handle(
        client, "add a task called Ship v1 to Q3 Marketing Campaign with urgent priority"
    )
    assert "Ship v1" in reply
    task = next(iter(client.tasks.values()))
    assert task["title"] == "Ship v1"
    assert task["priority"] == "urgent"


def test_create_task_unknown_project() -> None:
    client = FakeClient()
    reply = handle(client, "add task Something to Nonexistent")
    assert "couldn't find" in reply.lower()
    assert client.tasks == {}


def test_tasks_by_status_across_projects() -> None:
    client = FakeClient()
    p = client.create_project("Alpha")
    client.create_task(p["id"], title="A", status="blocked")
    client.create_task(p["id"], title="B", status="todo")

    reply = handle(client, "what's blocked?")
    assert "blocked" in reply.lower()
    assert "A" in reply
    assert "B" not in reply.split("blocked", 1)[-1] or "1 task" in reply.lower()


def test_tasks_in_specific_project() -> None:
    client = FakeClient()
    p = client.create_project("Marketing")
    client.create_task(p["id"], title="Email sequence", status="in_progress")
    reply = handle(client, "show tasks in Marketing")
    assert "Email sequence" in reply


def test_summary() -> None:
    client = FakeClient()
    p = client.create_project("Alpha")
    client.create_task(p["id"], title="A", status="done")
    reply = handle(client, "summary")
    assert "Alpha" in reply
    assert "1 task" in reply


def test_assigned_to_person() -> None:
    client = FakeClient()
    p = client.create_project("Alpha")
    client.create_task(p["id"], title="Build nav", assignee="Alice")
    client.create_task(p["id"], title="Write docs", assignee="Bob")

    reply = handle(client, "who is working on Alice?")
    assert "Build nav" in reply
    assert "Write docs" not in reply

    miss = handle(client, "assigned to Nobody")
    assert "couldn't find" in miss.lower()


def test_unknown_message() -> None:
    client = FakeClient()
    assert "not sure" in handle(client, "make me a sandwich").lower()
