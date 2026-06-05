"""Data access for bills, delegating to a storage backend."""
from __future__ import annotations

from typing import Any

from app.db.repositories.base import BaseRepository

PARTITION_KEY_FIELD = "building_id"
CONTAINER_NAME = "bills"


class BillRepository:
    def __init__(self, backend: BaseRepository) -> None:
        self._backend = backend

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.create(document)

    async def get(self, bill_id: str, building_id: str) -> dict[str, Any] | None:
        return await self._backend.get(bill_id, building_id)

    async def list_for_building(
        self,
        building_id: str,
        period: str | None = None,
        status: str | None = None,
        bill_type: str | None = None,
        tenant_id: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {"building_id": building_id}
        if period is not None:
            filters["period"] = period
        if status is not None:
            filters["status"] = status
        if bill_type is not None:
            filters["bill_type"] = bill_type
        if tenant_id is not None:
            filters["tenant_id"] = tenant_id
        return await self._backend.query(filters, limit=limit, offset=offset)

    async def update(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.update(document)

    async def delete(self, bill_id: str, building_id: str) -> bool:
        return await self._backend.delete(bill_id, building_id)
