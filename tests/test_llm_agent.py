"""Tests for the Ollama tool executor and backend selection / fallback.

These do not hit a live Ollama server — the LLM call is monkeypatched. They
verify the deterministic glue: tool dispatch and graceful degradation.
"""
from __future__ import annotations

import pytest

from tests.test_chat_engine import FakeClient
from app.chat import assistant, llm_agent


# --- tool executor ---

def test_execute_list_buildings() -> None:
    client = FakeClient()
    b = client.add_building("Lakeview", city="Pune")
    client.add_unit(b["id"], "1", status="occupied")
    client.add_unit(b["id"], "2", status="vacant")
    result = llm_agent.execute_tool(client, "list_buildings", {})
    assert result["buildings"][0]["name"] == "Lakeview"
    assert result["buildings"][0]["units"] == 2
    assert result["buildings"][0]["occupied"] == 1


def test_execute_list_tenants_resolves_building() -> None:
    client = FakeClient()
    b = client.add_building("Green Meadows")
    client.add_tenant(b["id"], "Anjali")
    result = llm_agent.execute_tool(client, "list_tenants", {"building_name": "green"})
    assert result["building"] == "Green Meadows"
    assert [t["name"] for t in result["tenants"]] == ["Anjali"]


def test_execute_list_tenants_unknown_building() -> None:
    result = llm_agent.execute_tool(FakeClient(), "list_tenants", {"building_name": "Ghost"})
    assert "error" in result


def test_execute_overdue_bills_across_buildings() -> None:
    client = FakeClient()
    a = client.add_building("A")
    b = client.add_building("B")
    client.add_bill(a["id"], status="overdue", tenant_name="X")
    client.add_bill(b["id"], status="partial", tenant_name="Y")
    client.add_bill(b["id"], status="paid", tenant_name="Z")
    result = llm_agent.execute_tool(client, "overdue_bills", {})
    names = sorted(item["tenant"] for item in result["outstanding"])
    assert names == ["X", "Y"]


def test_execute_unknown_tool() -> None:
    assert "error" in llm_agent.execute_tool(FakeClient(), "frobnicate", {})


# --- backend selection / fallback ---

def test_respond_forces_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assistant, "CHAT_BACKEND", "rules")
    reply, backend = assistant.respond(FakeClient(), "help")
    assert backend == "rules"
    assert "manage your rentals" in reply


def test_auto_falls_back_when_ollama_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assistant, "CHAT_BACKEND", "auto")
    monkeypatch.setattr(llm_agent, "is_available", lambda *a, **k: False)
    reply, backend = assistant.respond(FakeClient(), "list my buildings")
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
