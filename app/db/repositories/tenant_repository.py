"""Data access for tenants, delegating to a storage backend."""
from __future__ import annotations

from typing import Any

from app.db.repositories.base import BaseRepository

PARTITION_KEY_FIELD = "building_id"
CONTAINER_NAME = "tenants"


class TenantRepository:
    def __init__(self, backend: BaseRepository) -> None:
        self._backend = backend

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.create(document)

    async def get(self, tenant_id: str, building_id: str) -> dict[str, Any] | None:
        return await self._backend.get(tenant_id, building_id)

    async def list_for_building(
        self, building_id: str, limit: int = 500, offset: int = 0
    ) -> list[dict[str, Any]]:
        return await self._backend.query(
            {"building_id": building_id}, limit=limit, offset=offset
        )

    async def update(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.update(document)

    async def delete(self, tenant_id: str, building_id: str) -> bool:
        return await self._backend.delete(tenant_id, building_id)
