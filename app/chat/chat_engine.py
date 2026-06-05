"""Rule-based chat assistant for the Task Tracker.

Parses a user's natural-language message, calls the API to fulfil the intent,
and returns a plain-text reply. No external AI service is used — intents are
matched with simple, deterministic rules, which keeps the demo zero-cost and
fully offline.

The engine only depends on an object exposing the ApiClient methods
(``list_projects``, ``create_project``, ``list_tasks``, ``create_task``), so it
can be unit-tested with a lightweight fake.
"""
from __future__ import annotations

import re
from typing import Any, Protocol

STATUS_ALIASES = {
    "todo": "todo",
    "to do": "todo",
    "to-do": "todo",
    "in progress": "in_progress",
    "in-progress": "in_progress",
    "ongoing": "in_progress",
    "blocked": "blocked",
    "stuck": "blocked",
    "done": "done",
    "completed": "done",
    "finished": "done",
}

PRIORITY_WORDS = {"low", "medium", "high", "urgent"}

HELP_TEXT = (
    "I can help you manage projects and tasks. Try:\n"
    "  • *list my projects*\n"
    "  • *create project Marketing Site*\n"
    "  • *show tasks in Website Redesign*\n"
    "  • *what's blocked?*\n"
    "  • *add task Write docs to Website Redesign (priority high)*\n"
    "  • *summary*"
)


class SupportsApi(Protocol):
    def list_projects(self) -> list[dict[str, Any]]: ...
    def create_project(self, name: str, description: str | None = ...) -> dict[str, Any]: ...
    def list_tasks(self, project_id: str, status: str | None = ...) -> list[dict[str, Any]]: ...
    def create_task(self, project_id: str, title: str, **kwargs: Any) -> dict[str, Any]: ...


def _find_status(text: str) -> str | None:
    """Return the canonical status if a status phrase appears in the text."""
    lowered = text.lower()
    # Prefer multi-word matches first (e.g. "in progress" before "progress").
    for alias in sorted(STATUS_ALIASES, key=len, reverse=True):
        if alias in lowered:
            return STATUS_ALIASES[alias]
    return None


def _resolve_project(client: SupportsApi, name: str) -> dict[str, Any] | None:
    """Match a project by name (case-insensitive exact, then substring)."""
    name = name.strip().strip("\"'").lower()
    projects = client.list_projects()
    for project in projects:
        if project["name"].lower() == name:
            return project
    for project in projects:
        if name in project["name"].lower():
            return project
    return None


def _extract_priority(text: str) -> tuple[str, str]:
    """Pull a priority hint out of the text; return (cleaned_text, priority).

    Handles both word orders and an optional leading 'with'/'at', e.g.
    'priority high', 'with high priority', '(urgent)'.
    """
    pattern = (
        r"\s*(?:\bwith\b|\bat\b)?\s*\(?\b"
        r"(?:priority[:=]?\s+(?P<a>low|medium|high|urgent)"
        r"|(?P<b>low|medium|high|urgent)\s+priority)\b\)?"
    )
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return text, "medium"
    priority = (match.group("a") or match.group("b")).lower()
    cleaned = (text[: match.start()] + " " + text[match.end() :]).strip(" ()")
    return re.sub(r"\s{2,}", " ", cleaned), priority


def _format_tasks(tasks: list[dict[str, Any]]) -> str:
    if not tasks:
        return "  (no tasks)"
    lines = []
    for t in tasks:
        who = f" — @{t['assignee']}" if t.get("assignee") else ""
        lines.append(f"  • [{t['status']}] {t['title']} ({t['priority']}){who}")
    return "\n".join(lines)


def handle(client: SupportsApi, message: str) -> str:
    """Route a message to an intent handler and return a reply string."""
    text = message.strip()
    if not text:
        return "Say something — type *help* to see what I can do."

    lowered = text.lower()

    if lowered in {"help", "?", "what can you do", "what can you do?"}:
        return HELP_TEXT

    if lowered in {"hi", "hello", "hey", "yo"}:
        return "Hi! I'm your task assistant. Type *help* for examples."

    # --- create task: "add task <title> to <project>" ---
    # Pull any "priority X" hint out first so it can appear anywhere in the message.
    text_wo_priority, priority = _extract_priority(text)
    m = re.match(
        r"(?:create|add|new)\s+(?:a\s+|an\s+)?task\s+(?:called\s+|named\s+|titled\s+)?"
        r"(.+?)\s+(?:to|in|under|for)\s+(?:project\s+)?(.+)$",
        text_wo_priority,
        re.IGNORECASE,
    )
    if m:
        raw_title, project_name = m.group(1), m.group(2)
        title = raw_title.strip().strip("\"'")
        project = _resolve_project(client, project_name)
        if project is None:
            return f"I couldn't find a project matching '{project_name.strip()}'."
        task = client.create_task(project["id"], title=title, priority=priority)
        return f"Added task '{task['title']}' ({priority}) to {project['name']}."

    # --- create project: "create project <name>" ---
    m = re.match(
        r"(?:create|add|new)\s+(?:a\s+|an\s+)?project\s+(?:called\s+|named\s+)?(.+)$",
        text,
        re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip().strip("\"'")
        project = client.create_project(name)
        return f"Created project '{project['name']}'."

    # --- tasks in a specific project: "show tasks in <project>" ---
    m = re.search(
        r"tasks?\s+(?:in|for|under|of)\s+(?:project\s+)?(.+)$", text, re.IGNORECASE
    )
    if m:
        project_name = m.group(1)
        status = _find_status(project_name)
        # Strip a trailing status phrase from the captured project name if present.
        project = _resolve_project(client, re.sub(r"\b(that are|which are)\b.*", "", project_name))
        if project is None:
            return f"I couldn't find a project matching '{project_name.strip()}'."
        tasks = client.list_tasks(project["id"], status=status)
        header = f"Tasks in {project['name']}" + (f" [{status}]" if status else "") + ":"
        return f"{header}\n{_format_tasks(tasks)}"

    # --- tasks by status across all projects: "what's blocked", "show done tasks" ---
    status = _find_status(lowered)
    if status and ("task" in lowered or "what" in lowered or "show" in lowered or "list" in lowered):
        projects = client.list_projects()
        chunks = []
        total = 0
        for project in projects:
            tasks = client.list_tasks(project["id"], status=status)
            if tasks:
                total += len(tasks)
                chunks.append(f"{project['name']}:\n{_format_tasks(tasks)}")
        if total == 0:
            return f"No tasks are currently *{status}*."
        return f"{total} task(s) *{status}*:\n\n" + "\n\n".join(chunks)

    # --- summary / overview ---
    if any(w in lowered for w in ("summary", "overview", "how many", "status report")):
        projects = client.list_projects()
        if not projects:
            return "You have no projects yet. Try *create project My First Project*."
        lines = [f"You have {len(projects)} project(s):"]
        for project in projects:
            tasks = client.list_tasks(project["id"])
            counts: dict[str, int] = {}
            for t in tasks:
                counts[t["status"]] = counts.get(t["status"], 0) + 1
            breakdown = ", ".join(f"{v} {k}" for k, v in counts.items()) or "no tasks"
            lines.append(f"  • {project['name']} — {len(tasks)} task(s) ({breakdown})")
        return "\n".join(lines)

    # --- list projects ---
    if "project" in lowered and any(w in lowered for w in ("list", "show", "my", "all", "what")):
        projects = client.list_projects()
        if not projects:
            return "You have no projects yet. Try *create project My First Project*."
        listing = "\n".join(f"  • {p['name']}" for p in projects)
        return f"Your projects:\n{listing}"

    return (
        "I'm not sure how to help with that. Type *help* to see what I can do."
    )
