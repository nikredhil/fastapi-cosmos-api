"""Business logic for projects."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from app.db.repositories.project_repository import ProjectRepository
from app.models.schemas.project import Project, ProjectCreate, ProjectUpdate


class ProjectNotFoundError(Exception):
    """Raised when a project does not exist or is not owned by the caller."""


def _derive_key_prefix(name: str) -> str:
    """Build a short uppercase item-key prefix from a project name.

    Multi-word names use the leading initials (e.g. "Website Migration" -> "WM");
    a single word uses its first three letters (e.g. "Payments" -> "PAY").
    """
    words = re.findall(r"[A-Za-z0-9]+", name)
    if not words:
        return "TT"
    if len(words) >= 2:
        return "".join(w[0] for w in words[:4]).upper()
    return words[0][:3].upper()


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repo = repository

    async def create(self, owner: str, payload: ProjectCreate) -> Project:
        now = datetime.now(timezone.utc)
        document = {
            "id": str(uuid.uuid4()),
            "owner": owner,
            "name": payload.name,
            "description": payload.description,
            "key_prefix": _derive_key_prefix(payload.name),
            "task_counter": 0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        created = await self._repo.create(document)
        return Project(**created)

    async def next_item_number(self, owner: str, project_id: str) -> tuple[int, str]:
        """Allocate and persist the next per-project item number; return (number, key).

        Simple read-modify-write — adequate for the single-user demo, not hardened
        against concurrent writers.
        """
        doc = await self._repo.get(project_id, owner)
        if doc is None:
            raise ProjectNotFoundError(project_id)
        number = int(doc.get("task_counter", 0)) + 1
        prefix = doc.get("key_prefix") or _derive_key_prefix(doc.get("name", ""))
        doc["task_counter"] = number
        doc["key_prefix"] = prefix
        await self._repo.update(doc)
        return number, f"{prefix}-{number}"

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
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = await self._repo.update(doc)
        return Project(**updated)

    async def delete(self, owner: str, project_id: str) -> None:
        deleted = await self._repo.delete(project_id, owner)
        if not deleted:
            raise ProjectNotFoundError(project_id)
