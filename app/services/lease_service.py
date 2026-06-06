"""Business logic for leases/contracts."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.repositories.lease_repository import LeaseRepository
from app.models.schemas.lease import Lease, LeaseCreate, LeaseUpdate
from app.services.building_service import BuildingNotFoundError, BuildingService
from app.services.unit_service import UnitService


class LeaseNotFoundError(Exception):
    """Raised when a lease does not exist within the given building."""


class LeaseService:
    def __init__(
        self, repository: LeaseRepository, building_service: BuildingService,
        unit_service: UnitService,
    ) -> None:
        self._repo = repository
        self._buildings = building_service
        self._units = unit_service

    async def _assert_building(self, owner: str, building_id: str) -> None:
        await self._buildings.get(owner, building_id)

    async def create(self, owner: str, building_id: str, payload: LeaseCreate) -> Lease:
        await self._assert_building(owner, building_id)
        now = datetime.now(timezone.utc)
        document = {
            "id": str(uuid.uuid4()),
            "building_id": building_id,
            "unit_id": payload.unit_id,
            "tenant_id": payload.tenant_id,
            "start_date": payload.start_date,
            "end_date": payload.end_date,
            "monthly_rent": payload.monthly_rent,
            "deposit": payload.deposit,
            "rent_due_day": payload.rent_due_day,
            "lease_months": payload.lease_months,
            "rent_increase_pct": payload.rent_increase_pct,
            "terms": payload.terms,
            "contract_image_id": payload.contract_image_id,
            "parsed": payload.parsed,
            "status": "active",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        created = await self._repo.create(document)
        if payload.unit_id:
            await self._units.set_status(owner, building_id, payload.unit_id, "occupied")
        return Lease(**created)

    async def get(self, owner: str, building_id: str, lease_id: str) -> Lease:
        await self._assert_building(owner, building_id)
        doc = await self._repo.get(lease_id, building_id)
        if doc is None:
            raise LeaseNotFoundError(lease_id)
        return Lease(**doc)

    async def list(self, owner: str, building_id: str, limit: int, offset: int) -> list[Lease]:
        await self._assert_building(owner, building_id)
        docs = await self._repo.list_for_building(building_id, limit=limit, offset=offset)
        docs.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        return [Lease(**d) for d in docs]

    async def update(
        self, owner: str, building_id: str, lease_id: str, payload: LeaseUpdate
    ) -> Lease:
        await self._assert_building(owner, building_id)
        doc = await self._repo.get(lease_id, building_id)
        if doc is None:
            raise LeaseNotFoundError(lease_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            doc[key] = value.value if hasattr(value, "value") else value
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = await self._repo.update(doc)
        return Lease(**updated)

    async def delete(self, owner: str, building_id: str, lease_id: str) -> None:
        await self._assert_building(owner, building_id)
        deleted = await self._repo.delete(lease_id, building_id)
        if not deleted:
            raise LeaseNotFoundError(lease_id)


__all__ = ["LeaseService", "LeaseNotFoundError"]
