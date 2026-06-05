"""Data access for leases/contracts, delegating to a storage backend."""
from __future__ import annotations

from typing import Any

from app.db.repositories.base import BaseRepository

PARTITION_KEY_FIELD = "building_id"
CONTAINER_NAME = "leases"


class LeaseRepository:
    def __init__(self, backend: BaseRepository) -> None:
        self._backend = backend

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.create(document)

    async def get(self, lease_id: str, building_id: str) -> dict[str, Any] | None:
        return await self._backend.get(lease_id, building_id)

    async def list_for_building(
        self, building_id: str, limit: int = 500, offset: int = 0
    ) -> list[dict[str, Any]]:
        return await self._backend.query(
            {"building_id": building_id}, limit=limit, offset=offset
        )

    async def update(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.update(document)

    async def delete(self, lease_id: str, building_id: str) -> bool:
        return await self._backend.delete(lease_id, building_id)
