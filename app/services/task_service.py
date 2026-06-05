"""Business logic for tasks."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.db.repositories.task_repository import TaskRepository
from app.models.schemas.task import Task, TaskCreate, TaskUpdate
from app.services.project_service import ProjectNotFoundError, ProjectService


class TaskNotFoundError(Exception):
    """Raised when a task does not exist within the given project."""


class TaskService:
    def __init__(self, repository: TaskRepository, project_service: ProjectService) -> None:
        self._repo = repository
        self._projects = project_service

    async def _assert_project(self, owner: str, project_id: str) -> None:
        # Raises ProjectNotFoundError if the caller doesn't own the parent project.
        await self._projects.get(owner, project_id)

    async def create(self, owner: str, project_id: str, payload: TaskCreate) -> Task:
        await self._assert_project(owner, project_id)
        now = datetime.now(UTC)
        document = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "title": payload.title,
            "description": payload.description,
            "status": payload.status.value,
            "priority": payload.priority.value,
            "assignee": payload.assignee,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        created = await self._repo.create(document)
        return Task(**created)

    async def get(self, owner: str, project_id: str, task_id: str) -> Task:
        await self._assert_project(owner, project_id)
        doc = await self._repo.get(task_id, project_id)
        if doc is None:
            raise TaskNotFoundError(task_id)
        return Task(**doc)

    async def list(
        self, owner: str, project_id: str, status: str | None, limit: int, offset: int
    ) -> list[Task]:
        await self._assert_project(owner, project_id)
        docs = await self._repo.list_for_project(
            project_id, status=status, limit=limit, offset=offset
        )
        return [Task(**d) for d in docs]

    async def update(
        self, owner: str, project_id: str, task_id: str, payload: TaskUpdate
    ) -> Task:
        await self._assert_project(owner, project_id)
        doc = await self._repo.get(task_id, project_id)
        if doc is None:
            raise TaskNotFoundError(task_id)

        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            # Enum fields serialize to their string value for storage.
            doc[key] = value.value if hasattr(value, "value") else value
        doc["updated_at"] = datetime.now(UTC).isoformat()
        updated = await self._repo.update(doc)
        return Task(**updated)

    async def delete(self, owner: str, project_id: str, task_id: str) -> None:
        await self._assert_project(owner, project_id)
        deleted = await self._repo.delete(task_id, project_id)
        if not deleted:
            raise TaskNotFoundError(task_id)


__all__ = ["TaskService", "TaskNotFoundError", "ProjectNotFoundError"]
