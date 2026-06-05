"""Ollama-backed tool-calling assistant.

The LLM is given a set of tools (list/create projects and tasks). It decides
which to call; this module executes the calls against the Task Tracker API,
feeds the results back, and loops until the model produces a final answer.

Uses Ollama's HTTP API directly (no extra dependency). Works with any
tool-capable model — set OLLAMA_MODEL (e.g. "llama3.2", "gpt-oss:120b-cloud").
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx

from app.chat.chat_engine import SupportsApi, _resolve_project

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
MAX_STEPS = 6

SYSTEM_PROMPT = (
    "You are an assistant for a task-tracking app. The signed-in user owns a set of "
    "projects, each containing tasks.\n"
    "ALWAYS use the tools to answer questions about the user's projects or tasks — "
    "never answer from general knowledge, and never invent project names, task "
    "titles, ids, statuses, or counts. If a question is about what is blocked / in "
    "progress / done across everything, call find_tasks_by_status.\n"
    "When the user asks to create something and has given the required details "
    "(a project name, and a title for a task), create it immediately with the tools. "
    "Do NOT ask for optional fields such as assignee or description — leave them "
    "empty if the user didn't mention them.\n"
    "Task status is one of: todo, in_progress, blocked, done. Priority is one of: "
    "low, medium, high, urgent. Keep replies concise and friendly."
)

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_projects",
            "description": "List all of the user's projects.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List tasks in a project, optionally filtered by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["todo", "in_progress", "blocked", "done"],
                    },
                },
                "required": ["project_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_tasks_by_status",
            "description": (
                "Find all tasks across every project that have the given status. "
                "Use this for questions like 'what's blocked?' or 'what's in progress?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["todo", "in_progress", "blocked", "done"],
                    },
                },
                "required": ["status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "Create a new project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a task inside an existing project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "title": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["todo", "in_progress", "blocked", "done"],
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                    },
                    "assignee": {"type": "string"},
                },
                "required": ["project_name", "title"],
            },
        },
    },
]


def execute_tool(client: SupportsApi, name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Run one tool call against the API. Returns a JSON-serializable result.

    Pure dispatch with no model dependency, so it is unit-testable directly.
    """
    if name == "list_projects":
        projects = client.list_projects()
        return {"projects": [{"name": p["name"]} for p in projects]}

    if name == "create_project":
        project = client.create_project(args["name"], args.get("description"))
        return {"created": project["name"]}

    if name == "find_tasks_by_status":
        status = args.get("status")
        matches = []
        for project in client.list_projects():
            for task in client.list_tasks(project["id"], status=status):
                matches.append(
                    {
                        "project": project["name"],
                        "title": task["title"],
                        "priority": task["priority"],
                        "assignee": task.get("assignee"),
                    }
                )
        return {"status": status, "tasks": matches}

    if name in ("list_tasks", "create_task"):
        target = _resolve_project(client, args.get("project_name", ""))
        if target is None:
            return {"error": f"No project matching '{args.get('project_name', '')}'."}

        if name == "list_tasks":
            tasks = client.list_tasks(target["id"], status=args.get("status"))
            return {
                "project": target["name"],
                "tasks": [
                    {
                        "title": t["title"],
                        "status": t["status"],
                        "priority": t["priority"],
                        "assignee": t.get("assignee"),
                    }
                    for t in tasks
                ],
            }

        task = client.create_task(
            target["id"],
            title=args["title"],
            status=args.get("status", "todo"),
            priority=args.get("priority", "medium"),
            assignee=args.get("assignee"),
        )
        return {"created_task": task["title"], "in_project": target["name"]}

    return {"error": f"Unknown tool '{name}'."}


def is_available(host: str = OLLAMA_HOST, timeout: float = 1.5) -> bool:
    """Return True if an Ollama server is reachable."""
    try:
        resp = httpx.get(f"{host.rstrip('/')}/api/tags", timeout=timeout)
        return resp.status_code == 200
    except Exception:  # noqa: BLE001 - any failure means "not available"
        return False


def _ollama_chat(messages: list[dict[str, Any]], model: str, host: str) -> dict[str, Any]:
    resp = httpx.post(
        f"{host.rstrip('/')}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "tools": TOOLS,
            "stream": False,
            "options": {"temperature": 0.3},
        },
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()["message"]


def chat(
    client: SupportsApi,
    message: str,
    history: list[dict[str, str]] | None = None,
    model: str = OLLAMA_MODEL,
    host: str = OLLAMA_HOST,
) -> str:
    """Run the tool-calling loop and return the assistant's final reply.

    Raises on transport errors so the caller can fall back to the rule engine.
    """
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history or []:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    for _ in range(MAX_STEPS):
        assistant_msg = _ollama_chat(messages, model, host)
        tool_calls = assistant_msg.get("tool_calls") or []

        if not tool_calls:
            return assistant_msg.get("content", "").strip() or "(no response)"

        messages.append(assistant_msg)
        for call in tool_calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            raw_args = fn.get("arguments", {})
            args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
            result = execute_tool(client, name, args)
            messages.append(
                {"role": "tool", "tool_name": name, "content": json.dumps(result)}
            )

    return "I wasn't able to complete that in a reasonable number of steps — please rephrase."
