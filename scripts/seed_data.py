"""Seed the API with sample projects, members, sprints, and work items.

The API now authenticates with Microsoft (Entra ID), so seeding needs a real
bearer token. Sign in to the web app, copy the ID token your browser sends in
the Authorization header (DevTools → Network → any /projects request), then:

    API_TOKEN="<id-token>" python scripts/seed_data.py
    API_BASE=http://localhost:8055 API_TOKEN="<id-token>" python scripts/seed_data.py
"""
from __future__ import annotations

import os
import sys

import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN")

# Per project: a roster of members, a couple of sprints, and work items.
# A work item is (title, item_type, status, priority, points, assignee, sprint, tags).
SAMPLE = {
    "Website Redesign": {
        "members": [
            ("Alice Chen", "Product Designer", "#6366f1"),
            ("Bob Singh", "Frontend Engineer", "#0ea5e9"),
            ("Carol Diaz", "Accessibility Lead", "#10b981"),
        ],
        "sprints": [
            ("Sprint 1 — Foundations", "active", "2026-06-01", "2026-06-14"),
            ("Sprint 2 — Polish", "planned", "2026-06-15", "2026-06-28"),
        ],
        "items": [
            ("Audit current site analytics", "task", "done", "medium", 3, "Alice Chen", 0, ["analytics"]),
            ("Wireframe new homepage", "story", "in_progress", "high", 8, "Alice Chen", 0, ["design"]),
            ("Design system + component library", "story", "in_progress", "high", 13, "Bob Singh", 0, ["design", "frontend"]),
            ("Migrate blog content", "task", "todo", "low", 5, None, 1, ["content"]),
            ("Accessibility (WCAG AA) pass", "task", "todo", "high", 8, "Carol Diaz", 1, ["a11y"]),
            ("Nav dropdown flickers on hover", "bug", "blocked", "urgent", 2, "Bob Singh", 0, ["frontend"]),
        ],
    },
    "Mobile App v2": {
        "members": [
            ("Alice Chen", "Tech Lead", "#6366f1"),
            ("Bob Singh", "Mobile Engineer", "#0ea5e9"),
            ("Carol Diaz", "QA", "#10b981"),
        ],
        "sprints": [
            ("Sprint A — Core", "active", "2026-06-02", "2026-06-16"),
        ],
        "items": [
            ("Set up CI/CD pipeline", "task", "done", "high", 5, "Bob Singh", 0, ["devops"]),
            ("Offline mode sync engine", "story", "blocked", "urgent", 13, "Alice Chen", 0, ["sync"]),
            ("Push notifications", "story", "todo", "medium", 8, "Carol Diaz", 0, ["notifications"]),
            ("App Store screenshots", "task", "todo", "low", 2, None, None, ["release"]),
        ],
    },
    "Q3 Marketing Campaign": {
        "members": [
            ("Carol Diaz", "Campaign Manager", "#10b981"),
            ("Alice Chen", "Copywriter", "#6366f1"),
        ],
        "sprints": [
            ("Launch Sprint", "active", "2026-06-03", "2026-06-17"),
        ],
        "items": [
            ("Define target segments", "task", "done", "medium", 3, "Carol Diaz", 0, ["research"]),
            ("Draft email sequence", "story", "in_progress", "medium", 5, "Alice Chen", 0, ["email"]),
            ("Landing page A/B test", "story", "todo", "high", 8, None, 0, ["web"]),
        ],
    },
}


def main() -> None:
    if not API_TOKEN:
        sys.exit(
            "API_TOKEN is required. Sign in to the web app, copy the bearer token from a "
            "/projects request (DevTools → Network), and re-run with API_TOKEN=<token>."
        )
    with httpx.Client(base_url=API_BASE, timeout=10.0) as client:
        headers = {"Authorization": f"Bearer {API_TOKEN}"}

        n_projects = n_members = n_sprints = n_items = 0
        for project_name, spec in SAMPLE.items():
            pid = client.post(
                "/projects", json={"name": project_name}, headers=headers
            ).json()["id"]
            n_projects += 1

            # Members → name -> id lookup.
            member_ids: dict[str, str] = {}
            for name, role, color in spec["members"]:
                member = client.post(
                    f"/projects/{pid}/members",
                    json={"name": name, "role": role, "avatar_color": color},
                    headers=headers,
                ).json()
                member_ids[name] = member["id"]
                n_members += 1

            # Sprints → list of ids (referenced by index in items).
            sprint_ids: list[str] = []
            for name, sprint_status, start, end in spec["sprints"]:
                sprint = client.post(
                    f"/projects/{pid}/sprints",
                    json={"name": name, "start_date": start, "end_date": end},
                    headers=headers,
                ).json()
                if sprint_status != "planned":
                    client.patch(
                        f"/projects/{pid}/sprints/{sprint['id']}",
                        json={"status": sprint_status},
                        headers=headers,
                    )
                sprint_ids.append(sprint["id"])
                n_sprints += 1

            for title, item_type, status, priority, points, assignee, sprint_idx, tags in spec["items"]:
                client.post(
                    f"/projects/{pid}/tasks",
                    json={
                        "title": title,
                        "item_type": item_type,
                        "status": status,
                        "priority": priority,
                        "points": points,
                        "assignee_id": member_ids.get(assignee) if assignee else None,
                        "sprint_id": sprint_ids[sprint_idx] if sprint_idx is not None else None,
                        "tags": tags,
                    },
                    headers=headers,
                )
                n_items += 1

        print(
            f"Seeded {n_projects} projects, {n_members} members, {n_sprints} sprints, "
            f"and {n_items} work items at {API_BASE}"
        )


if __name__ == "__main__":
    main()
