"""Business logic for buildings (a landlord's properties)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.repositories.building_repository import BuildingRepository
from app.models.schemas.building import Building, BuildingCreate, BuildingUpdate


class BuildingNotFoundError(Exception):
    """Raised when a building does not exist or is not owned by the caller."""


class BuildingService:
    def __init__(self, repository: BuildingRepository) -> None:
        self._repo = repository

    async def create(self, owner: str, payload: BuildingCreate) -> Building:
        now = datetime.now(timezone.utc)
        document = {
            "id": str(uuid.uuid4()),
            "owner": owner,
            "name": payload.name,
            "address": payload.address,
            "city": payload.city,
            "notes": payload.notes,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        created = await self._repo.create(document)
        return Building(**created)

    async def get(self, owner: str, building_id: str) -> Building:
        doc = await self._repo.get(building_id, owner)
        if doc is None:
            raise BuildingNotFoundError(building_id)
        return Building(**doc)

    async def list(self, owner: str, limit: int, offset: int) -> list[Building]:
        docs = await self._repo.list_for_owner(owner, limit=limit, offset=offset)
        docs.sort(key=lambda d: d.get("created_at", ""))
        return [Building(**d) for d in docs]

    async def update(self, owner: str, building_id: str, payload: BuildingUpdate) -> Building:
        doc = await self._repo.get(building_id, owner)
        if doc is None:
            raise BuildingNotFoundError(building_id)
        doc.update(payload.model_dump(exclude_unset=True))
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = await self._repo.update(doc)
        return Building(**updated)

    async def delete(self, owner: str, building_id: str) -> None:
        deleted = await self._repo.delete(building_id, owner)
        if not deleted:
            raise BuildingNotFoundError(building_id)


__all__ = ["BuildingService", "BuildingNotFoundError"]
