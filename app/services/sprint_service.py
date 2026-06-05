"""Business logic for sprints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.repositories.sprint_repository import SprintRepository
from app.models.domain.enums import SprintStatus
from app.models.schemas.sprint import Sprint, SprintCreate, SprintUpdate
from app.services.project_service import ProjectNotFoundError, ProjectService


class SprintNotFoundError(Exception):
    """Raised when a sprint does not exist within the given project."""


class SprintService:
    def __init__(self, repository: SprintRepository, project_service: ProjectService) -> None:
        self._repo = repository
        self._projects = project_service

    async def _assert_project(self, owner: str, project_id: str) -> None:
        await self._projects.get(owner, project_id)

    async def create(self, owner: str, project_id: str, payload: SprintCreate) -> Sprint:
        await self._assert_project(owner, project_id)
        now = datetime.now(timezone.utc).isoformat()
        document = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "name": payload.name,
            "goal": payload.goal,
            "start_date": payload.start_date,
            "end_date": payload.end_date,
            "status": SprintStatus.PLANNED.value,
            "created_at": now,
            "updated_at": now,
        }
        created = await self._repo.create(document)
        return Sprint(**created)

    async def get(self, owner: str, project_id: str, sprint_id: str) -> Sprint:
        await self._assert_project(owner, project_id)
        doc = await self._repo.get(sprint_id, project_id)
        if doc is None:
            raise SprintNotFoundError(sprint_id)
        return Sprint(**doc)

    async def list(self, owner: str, project_id: str, limit: int, offset: int) -> list[Sprint]:
        await self._assert_project(owner, project_id)
        docs = await self._repo.list_for_project(project_id, limit=limit, offset=offset)
        docs.sort(key=lambda d: d.get("created_at", ""))
        return [Sprint(**d) for d in docs]

    async def update(
        self, owner: str, project_id: str, sprint_id: str, payload: SprintUpdate
    ) -> Sprint:
        await self._assert_project(owner, project_id)
        doc = await self._repo.get(sprint_id, project_id)
        if doc is None:
            raise SprintNotFoundError(sprint_id)
        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            doc[key] = value.value if hasattr(value, "value") else value
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = await self._repo.update(doc)
        return Sprint(**updated)

    async def delete(self, owner: str, project_id: str, sprint_id: str) -> None:
        await self._assert_project(owner, project_id)
        deleted = await self._repo.delete(sprint_id, project_id)
        if not deleted:
            raise SprintNotFoundError(sprint_id)


__all__ = ["SprintService", "SprintNotFoundError"]
