"""Seed the API with sample projects and tasks via its HTTP interface.

Works against either backend. Start the server first, then run:

    python scripts/seed_data.py                  # uses http://localhost:8000
    API_BASE=http://localhost:8055 python scripts/seed_data.py
"""
from __future__ import annotations

import os

import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
USERNAME = os.getenv("SEED_USER", "demo")

SAMPLE = {
    "Website Redesign": [
        ("Audit current site analytics", "done", "medium", "alice"),
        ("Wireframe new homepage", "in_progress", "high", "alice"),
        ("Design system + component library", "in_progress", "high", "bob"),
        ("Migrate blog content", "todo", "low", None),
        ("Accessibility (WCAG AA) pass", "todo", "high", "carol"),
    ],
    "Mobile App v2": [
        ("Set up CI/CD pipeline", "done", "high", "bob"),
        ("Offline mode sync engine", "blocked", "urgent", "alice"),
        ("Push notifications", "todo", "medium", "carol"),
        ("App Store screenshots", "todo", "low", None),
    ],
    "Q3 Marketing Campaign": [
        ("Define target segments", "done", "medium", "carol"),
        ("Draft email sequence", "in_progress", "medium", "alice"),
        ("Landing page A/B test", "todo", "high", "bob"),
    ],
}


def main() -> None:
    with httpx.Client(base_url=API_BASE, timeout=10.0) as client:
        token = client.post("/auth/token", json={"username": USERNAME}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        created_projects = created_tasks = 0
        for project_name, tasks in SAMPLE.items():
            project = client.post(
                "/projects", json={"name": project_name}, headers=headers
            ).json()
            created_projects += 1
            pid = project["id"]
            for title, status, priority, assignee in tasks:
                client.post(
                    f"/projects/{pid}/tasks",
                    json={
                        "title": title,
                        "status": status,
                        "priority": priority,
                        "assignee": assignee,
                    },
                    headers=headers,
                )
                created_tasks += 1

        print(
            f"Seeded {created_projects} projects and {created_tasks} tasks "
            f"for user '{USERNAME}' at {API_BASE}"
        )


if __name__ == "__main__":
    main()
