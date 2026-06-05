"""Thin HTTP client for the Task Tracker API, used by the Streamlit UI."""
from __future__ import annotations

from typing import Any

import httpx


class ApiError(Exception):
    """Raised when the API returns a non-success status."""


class ApiClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token

    @property
    def token(self) -> str | None:
        return self._token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    def login(self, username: str) -> str:
        resp = httpx.post(f"{self.base_url}/auth/token", json={"username": username}, timeout=10.0)
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        resp = httpx.request(
            method, f"{self.base_url}{path}", headers=self._headers(), timeout=10.0, **kwargs
        )
        if resp.status_code >= 400:
            raise ApiError(f"{resp.status_code}: {resp.text}")
        return resp

    # --- projects ---
    def list_projects(self) -> list[dict[str, Any]]:
        return self._request("GET", "/projects").json()["items"]

    def create_project(self, name: str, description: str | None = None) -> dict[str, Any]:
        body = {"name": name, "description": description}
        return self._request("POST", "/projects", json=body).json()

    # --- members & sprints ---
    def list_members(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/projects/{project_id}/members").json()["items"]

    def list_sprints(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/projects/{project_id}/sprints").json()["items"]

    # --- tasks ---
    def list_tasks(self, project_id: str, status: str | None = None) -> list[dict[str, Any]]:
        params = {"status": status} if status else None
        return self._request("GET", f"/projects/{project_id}/tasks", params=params).json()["items"]

    def create_task(
        self,
        project_id: str,
        title: str,
        status: str = "todo",
        priority: str = "medium",
        item_type: str = "task",
        points: int | None = None,
        assignee_id: str | None = None,
    ) -> dict[str, Any]:
        body = {
            "title": title,
            "status": status,
            "priority": priority,
            "item_type": item_type,
            "points": points,
            "assignee_id": assignee_id,
        }
        return self._request("POST", f"/projects/{project_id}/tasks", json=body).json()
