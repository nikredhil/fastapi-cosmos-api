"""Tests for the Ollama tool executor and backend selection / fallback.

These do not hit a live Ollama server — the LLM call is monkeypatched. They
verify the deterministic glue: tool dispatch and graceful degradation.
"""
from __future__ import annotations

import pytest

from tests.test_chat_engine import FakeClient
from app.chat import assistant, llm_agent


# --- tool executor ---

def test_execute_list_and_create_project() -> None:
    client = FakeClient()
    assert llm_agent.execute_tool(client, "create_project", {"name": "Alpha"}) == {
        "created": "Alpha"
    }
    result = llm_agent.execute_tool(client, "list_projects", {})
    assert result == {"projects": [{"name": "Alpha"}]}


def test_execute_create_task_resolves_project() -> None:
    client = FakeClient()
    client.create_project("Website")
    result = llm_agent.execute_tool(
        client,
        "create_task",
        {"project_name": "website", "title": "Build nav", "priority": "high"},
    )
    assert result == {"created_task": "Build nav", "in_project": "Website"}
    assert next(iter(client.tasks.values()))["priority"] == "high"


def test_execute_create_task_unknown_project() -> None:
    client = FakeClient()
    result = llm_agent.execute_tool(client, "create_task", {"project_name": "Ghost", "title": "x"})
    assert "error" in result
    assert client.tasks == {}


def test_execute_list_tasks_with_status() -> None:
    client = FakeClient()
    p = client.create_project("Alpha")
    client.create_task(p["id"], title="A", status="blocked")
    client.create_task(p["id"], title="B", status="todo")
    result = llm_agent.execute_tool(
        client, "list_tasks", {"project_name": "Alpha", "status": "blocked"}
    )
    assert [t["title"] for t in result["tasks"]] == ["A"]


def test_execute_find_tasks_by_status_across_projects() -> None:
    client = FakeClient()
    a = client.create_project("Alpha")
    b = client.create_project("Beta")
    client.create_task(a["id"], title="A1", status="blocked")
    client.create_task(b["id"], title="B1", status="blocked")
    client.create_task(b["id"], title="B2", status="todo")
    result = llm_agent.execute_tool(client, "find_tasks_by_status", {"status": "blocked"})
    titles = sorted(t["title"] for t in result["tasks"])
    assert titles == ["A1", "B1"]
    assert {t["project"] for t in result["tasks"]} == {"Alpha", "Beta"}


def test_execute_unknown_tool() -> None:
    assert "error" in llm_agent.execute_tool(FakeClient(), "frobnicate", {})


# --- backend selection / fallback ---

def test_respond_forces_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assistant, "CHAT_BACKEND", "rules")
    reply, backend = assistant.respond(FakeClient(), "help")
    assert backend == "rules"
    assert "manage projects" in reply


def test_auto_falls_back_when_ollama_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assistant, "CHAT_BACKEND", "auto")
    monkeypatch.setattr(llm_agent, "is_available", lambda *a, **k: False)
    reply, backend = assistant.respond(FakeClient(), "list my projects")
    assert backend == "rules"


def test_ollama_error_falls_back_to_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assistant, "CHAT_BACKEND", "ollama")

    def boom(*args, **kwargs):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(llm_agent, "chat", boom)
    reply, backend = assistant.respond(FakeClient(), "summary")
    assert backend == "rules"


def test_ollama_used_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assistant, "CHAT_BACKEND", "auto")
    monkeypatch.setattr(llm_agent, "is_available", lambda *a, **k: True)
    monkeypatch.setattr(llm_agent, "chat", lambda *a, **k: "Here is your answer.")
    reply, backend = assistant.respond(FakeClient(), "anything")
    assert backend == "ollama"
    assert reply == "Here is your answer."
