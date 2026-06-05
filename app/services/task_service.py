"""Business logic for tasks."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.repositories.task_repository import TaskRepository
from app.models.schemas.task import CommentCreate, Task, TaskCreate, TaskUpdate
from app.services.member_service import MemberNotFoundError, MemberService
from app.services.project_service import ProjectNotFoundError, ProjectService


class TaskNotFoundError(Exception):
    """Raised when a task does not exist within the given project."""


class TaskService:
    def __init__(
        self,
        repository: TaskRepository,
        project_service: ProjectService,
        member_service: MemberService,
    ) -> None:
        self._repo = repository
        self._projects = project_service
        self._members = member_service

    async def _assert_project(self, owner: str, project_id: str) -> None:
        # Raises ProjectNotFoundError if the caller doesn't own the parent project.
        await self._projects.get(owner, project_id)

    async def _resolve_assignee_name(
        self, owner: str, project_id: str, assignee_id: str | None
    ) -> str | None:
        """Look up a member's display name; returns None if unassigned/unknown."""
        if not assignee_id:
            return None
        try:
            member = await self._members.get(owner, project_id, assignee_id)
        except MemberNotFoundError:
            return None
        return member.name

    async def create(self, owner: str, project_id: str, payload: TaskCreate) -> Task:
        await self._assert_project(owner, project_id)
        now = datetime.now(timezone.utc)
        number, key = await self._projects.next_item_number(owner, project_id)
        assignee_name = await self._resolve_assignee_name(
            owner, project_id, payload.assignee_id
        )
        document = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "number": number,
            "key": key,
            "title": payload.title,
            "description": payload.description,
            "status": payload.status.value,
            "priority": payload.priority.value,
            "item_type": payload.item_type.value,
            "points": payload.points,
            "sprint_id": payload.sprint_id,
            "assignee_id": payload.assignee_id,
            "assignee_name": assignee_name,
            "due_date": payload.due_date,
            "tags": payload.tags,
            "comments": [],
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
        self,
        owner: str,
        project_id: str,
        status: str | None,
        sprint_id: str | None,
        assignee_id: str | None,
        limit: int,
        offset: int,
    ) -> list[Task]:
        await self._assert_project(owner, project_id)
        docs = await self._repo.list_for_project(
            project_id,
            status=status,
            sprint_id=sprint_id,
            assignee_id=assignee_id,
            limit=limit,
            offset=offset,
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
        # Keep the denormalized assignee name in sync when the assignee changes.
        if "assignee_id" in changes:
            doc["assignee_name"] = await self._resolve_assignee_name(
                owner, project_id, changes["assignee_id"]
            )
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = await self._repo.update(doc)
        return Task(**updated)

    async def add_comment(
        self, owner: str, project_id: str, task_id: str, payload: CommentCreate
    ) -> Task:
        await self._assert_project(owner, project_id)
        doc = await self._repo.get(task_id, project_id)
        if doc is None:
            raise TaskNotFoundError(task_id)
        comment = {
            "id": str(uuid.uuid4()),
            "author": owner,
            "body": payload.body,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        doc.setdefault("comments", []).append(comment)
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = await self._repo.update(doc)
        return Task(**updated)

    async def delete(self, owner: str, project_id: str, task_id: str) -> None:
        await self._assert_project(owner, project_id)
        deleted = await self._repo.delete(task_id, project_id)
        if not deleted:
            raise TaskNotFoundError(task_id)


__all__ = ["TaskService", "TaskNotFoundError", "ProjectNotFoundError"]
