"""Data access for project members, delegating to a storage backend."""
from __future__ import annotations

from typing import Any

from app.db.repositories.base import BaseRepository

PARTITION_KEY_FIELD = "project_id"
CONTAINER_NAME = "members"


class MemberRepository:
    def __init__(self, backend: BaseRepository) -> None:
        self._backend = backend

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.create(document)

    async def get(self, member_id: str, project_id: str) -> dict[str, Any] | None:
        return await self._backend.get(member_id, project_id)

    async def list_for_project(
        self, project_id: str, limit: int = 200, offset: int = 0
    ) -> list[dict[str, Any]]:
        return await self._backend.query(
            {"project_id": project_id}, limit=limit, offset=offset
        )

    async def update(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.update(document)

    async def delete(self, member_id: str, project_id: str) -> bool:
        return await self._backend.delete(member_id, project_id)
