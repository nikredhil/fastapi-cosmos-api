"""Business logic for project members (employees)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.repositories.member_repository import MemberRepository
from app.models.schemas.member import Member, MemberCreate, MemberUpdate
from app.services.project_service import ProjectNotFoundError, ProjectService

# A pleasant default palette cycled through when no avatar color is supplied.
_PALETTE = [
    "#6366f1", "#0ea5e9", "#10b981", "#f59e0b",
    "#ef4444", "#ec4899", "#8b5cf6", "#14b8a6",
]


class MemberNotFoundError(Exception):
    """Raised when a member does not exist within the given project."""


class MemberService:
    def __init__(self, repository: MemberRepository, project_service: ProjectService) -> None:
        self._repo = repository
        self._projects = project_service

    async def _assert_project(self, owner: str, project_id: str) -> None:
        await self._projects.get(owner, project_id)

    async def create(self, owner: str, project_id: str, payload: MemberCreate) -> Member:
        await self._assert_project(owner, project_id)
        existing = await self._repo.list_for_project(project_id, limit=1000)
        color = payload.avatar_color or _PALETTE[len(existing) % len(_PALETTE)]
        document = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "name": payload.name,
            "role": payload.role,
            "avatar_color": color,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        created = await self._repo.create(document)
        return Member(**created)

    async def get(self, owner: str, project_id: str, member_id: str) -> Member:
        await self._assert_project(owner, project_id)
        doc = await self._repo.get(member_id, project_id)
        if doc is None:
            raise MemberNotFoundError(member_id)
        return Member(**doc)

    async def list(self, owner: str, project_id: str, limit: int, offset: int) -> list[Member]:
        await self._assert_project(owner, project_id)
        docs = await self._repo.list_for_project(project_id, limit=limit, offset=offset)
        # Oldest first reads more naturally for a team roster.
        docs.sort(key=lambda d: d.get("created_at", ""))
        return [Member(**d) for d in docs]

    async def update(
        self, owner: str, project_id: str, member_id: str, payload: MemberUpdate
    ) -> Member:
        await self._assert_project(owner, project_id)
        doc = await self._repo.get(member_id, project_id)
        if doc is None:
            raise MemberNotFoundError(member_id)
        doc.update(payload.model_dump(exclude_unset=True))
        updated = await self._repo.update(doc)
        return Member(**updated)

    async def delete(self, owner: str, project_id: str, member_id: str) -> None:
        await self._assert_project(owner, project_id)
        deleted = await self._repo.delete(member_id, project_id)
        if not deleted:
            raise MemberNotFoundError(member_id)


__all__ = ["MemberService", "MemberNotFoundError"]
