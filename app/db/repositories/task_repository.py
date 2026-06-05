"""Data access for tasks, delegating to a storage backend."""
from __future__ import annotations

from typing import Any

from app.db.repositories.base import BaseRepository

PARTITION_KEY_FIELD = "project_id"
CONTAINER_NAME = "tasks"


class TaskRepository:
    def __init__(self, backend: BaseRepository) -> None:
        self._backend = backend

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.create(document)

    async def get(self, task_id: str, project_id: str) -> dict[str, Any] | None:
        return await self._backend.get(task_id, project_id)

    async def list_for_project(
        self,
        project_id: str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {"project_id": project_id}
        if status is not None:
            filters["status"] = status
        return await self._backend.query(filters, limit=limit, offset=offset)

    async def update(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.update(document)

    async def delete(self, task_id: str, project_id: str) -> bool:
        return await self._backend.delete(task_id, project_id)
