"""Data access for buildings, delegating to a storage backend."""
from __future__ import annotations

from typing import Any

from app.db.repositories.base import BaseRepository

PARTITION_KEY_FIELD = "owner"
CONTAINER_NAME = "buildings"


class BuildingRepository:
    def __init__(self, backend: BaseRepository) -> None:
        self._backend = backend

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.create(document)

    async def get(self, building_id: str, owner: str) -> dict[str, Any] | None:
        return await self._backend.get(building_id, owner)

    async def list_for_owner(
        self, owner: str, limit: int = 200, offset: int = 0
    ) -> list[dict[str, Any]]:
        return await self._backend.query({"owner": owner}, limit=limit, offset=offset)

    async def update(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.update(document)

    async def delete(self, building_id: str, owner: str) -> bool:
        return await self._backend.delete(building_id, owner)
