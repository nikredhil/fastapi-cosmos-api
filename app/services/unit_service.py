"""Business logic for units (flats within a building)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.repositories.unit_repository import UnitRepository
from app.models.schemas.unit import Unit, UnitCreate, UnitUpdate
from app.services.building_service import BuildingNotFoundError, BuildingService


class UnitNotFoundError(Exception):
    """Raised when a unit does not exist within the given building."""


class UnitService:
    def __init__(self, repository: UnitRepository, building_service: BuildingService) -> None:
        self._repo = repository
        self._buildings = building_service

    async def _assert_building(self, owner: str, building_id: str) -> None:
        await self._buildings.get(owner, building_id)

    async def create(self, owner: str, building_id: str, payload: UnitCreate) -> Unit:
        await self._assert_building(owner, building_id)
        now = datetime.now(timezone.utc)
        document = {
            "id": str(uuid.uuid4()),
            "building_id": building_id,
            "label": payload.label,
            "floor": payload.floor,
            "bedrooms": payload.bedrooms,
            "default_rent": payload.default_rent,
            "status": "vacant",
            "notes": payload.notes,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        created = await self._repo.create(document)
        return Unit(**created)

    async def get(self, owner: str, building_id: str, unit_id: str) -> Unit:
        await self._assert_building(owner, building_id)
        doc = await self._repo.get(unit_id, building_id)
        if doc is None:
            raise UnitNotFoundError(unit_id)
        return Unit(**doc)

    async def list(self, owner: str, building_id: str, limit: int, offset: int) -> list[Unit]:
        await self._assert_building(owner, building_id)
        docs = await self._repo.list_for_building(building_id, limit=limit, offset=offset)
        docs.sort(key=lambda d: d.get("label", ""))
        return [Unit(**d) for d in docs]

    async def update(
        self, owner: str, building_id: str, unit_id: str, payload: UnitUpdate
    ) -> Unit:
        await self._assert_building(owner, building_id)
        doc = await self._repo.get(unit_id, building_id)
        if doc is None:
            raise UnitNotFoundError(unit_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            doc[key] = value.value if hasattr(value, "value") else value
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = await self._repo.update(doc)
        return Unit(**updated)

    async def set_status(self, owner: str, building_id: str, unit_id: str, status: str) -> None:
        """Internal helper used when leases attach/detach a tenant to a unit."""
        doc = await self._repo.get(unit_id, building_id)
        if doc is None:
            return
        doc["status"] = status
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._repo.update(doc)

    async def delete(self, owner: str, building_id: str, unit_id: str) -> None:
        await self._assert_building(owner, building_id)
        deleted = await self._repo.delete(unit_id, building_id)
        if not deleted:
            raise UnitNotFoundError(unit_id)


__all__ = ["UnitService", "UnitNotFoundError"]
