"""Business logic for projects."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.db.repositories.project_repository import ProjectRepository
from app.models.schemas.project import Project, ProjectCreate, ProjectUpdate


class ProjectNotFoundError(Exception):
    """Raised when a project does not exist or is not owned by the caller."""


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repo = repository

    async def create(self, owner: str, payload: ProjectCreate) -> Project:
        now = datetime.now(UTC)
        document = {
            "id": str(uuid.uuid4()),
            "owner": owner,
            "name": payload.name,
            "description": payload.description,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        created = await self._repo.create(document)
        return Project(**created)

    async def get(self, owner: str, project_id: str) -> Project:
        doc = await self._repo.get(project_id, owner)
        if doc is None:
            raise ProjectNotFoundError(project_id)
        return Project(**doc)

    async def list(self, owner: str, limit: int, offset: int) -> list[Project]:
        docs = await self._repo.list_for_owner(owner, limit=limit, offset=offset)
        return [Project(**d) for d in docs]

    async def update(self, owner: str, project_id: str, payload: ProjectUpdate) -> Project:
        doc = await self._repo.get(project_id, owner)
        if doc is None:
            raise ProjectNotFoundError(project_id)

        changes = payload.model_dump(exclude_unset=True)
        doc.update(changes)
        doc["updated_at"] = datetime.now(UTC).isoformat()
        updated = await self._repo.update(doc)
        return Project(**updated)

    async def delete(self, owner: str, project_id: str) -> None:
        deleted = await self._repo.delete(project_id, owner)
        if not deleted:
            raise ProjectNotFoundError(project_id)
