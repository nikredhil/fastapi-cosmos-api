"""Business logic for tenants."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.repositories.tenant_repository import TenantRepository
from app.models.schemas.tenant import Tenant, TenantCreate, TenantUpdate
from app.services.building_service import BuildingNotFoundError, BuildingService
from app.services.unit_service import UnitService

# Trust-forward blue/teal palette, cycled when no avatar color is supplied.
_PALETTE = [
    "#2563eb", "#0ea5e9", "#0d9488", "#7c3aed",
    "#db2777", "#ea580c", "#16a34a", "#475569",
]


class TenantNotFoundError(Exception):
    """Raised when a tenant does not exist within the given building."""


class TenantService:
    def __init__(
        self, repository: TenantRepository, building_service: BuildingService,
        unit_service: UnitService,
    ) -> None:
        self._repo = repository
        self._buildings = building_service
        self._units = unit_service

    async def _assert_building(self, owner: str, building_id: str) -> None:
        await self._buildings.get(owner, building_id)

    async def create(self, owner: str, building_id: str, payload: TenantCreate) -> Tenant:
        await self._assert_building(owner, building_id)
        existing = await self._repo.list_for_building(building_id, limit=1000)
        color = payload.avatar_color or _PALETTE[len(existing) % len(_PALETTE)]
        now = datetime.now(timezone.utc)
        document = {
            "id": str(uuid.uuid4()),
            "building_id": building_id,
            "name": payload.name,
            "age": payload.age,
            "phone": payload.phone,
            "email": payload.email,
            "permanent_address": payload.permanent_address,
            "unit_id": payload.unit_id,
            "move_in_date": payload.move_in_date,
            "deposit": payload.deposit,
            "monthly_rent": payload.monthly_rent,
            "lease_months": payload.lease_months,
            "rent_increase_pct": payload.rent_increase_pct,
            "status": "active",
            "avatar_color": color,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        created = await self._repo.create(document)
        # Mark the occupied unit so dashboards reflect occupancy.
        if payload.unit_id:
            await self._units.set_status(owner, building_id, payload.unit_id, "occupied")
        return Tenant(**created)

    async def get(self, owner: str, building_id: str, tenant_id: str) -> Tenant:
        await self._assert_building(owner, building_id)
        doc = await self._repo.get(tenant_id, building_id)
        if doc is None:
            raise TenantNotFoundError(tenant_id)
        return Tenant(**doc)

    async def list(self, owner: str, building_id: str, limit: int, offset: int) -> list[Tenant]:
        await self._assert_building(owner, building_id)
        docs = await self._repo.list_for_building(building_id, limit=limit, offset=offset)
        docs.sort(key=lambda d: d.get("created_at", ""))
        return [Tenant(**d) for d in docs]

    async def update(
        self, owner: str, building_id: str, tenant_id: str, payload: TenantUpdate
    ) -> Tenant:
        await self._assert_building(owner, building_id)
        doc = await self._repo.get(tenant_id, building_id)
        if doc is None:
            raise TenantNotFoundError(tenant_id)
        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            doc[key] = value.value if hasattr(value, "value") else value
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = await self._repo.update(doc)
        if "unit_id" in changes and changes["unit_id"]:
            await self._units.set_status(owner, building_id, changes["unit_id"], "occupied")
        return Tenant(**updated)

    async def delete(self, owner: str, building_id: str, tenant_id: str) -> None:
        await self._assert_building(owner, building_id)
        doc = await self._repo.get(tenant_id, building_id)
        deleted = await self._repo.delete(tenant_id, building_id)
        if not deleted:
            raise TenantNotFoundError(tenant_id)
        if doc and doc.get("unit_id"):
            await self._units.set_status(owner, building_id, doc["unit_id"], "vacant")


__all__ = ["TenantService", "TenantNotFoundError"]
