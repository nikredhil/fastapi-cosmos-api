"""Business logic for bills (rent + utility charges) and payments."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.db.repositories.bill_repository import BillRepository
from app.models.domain.enums import BillType
from app.models.schemas.bill import (
    Bill,
    BillCreate,
    BillUpdate,
    GenerateBillsRequest,
    PaymentCreate,
)
from app.services.building_service import BuildingNotFoundError, BuildingService
from app.services.lease_service import LeaseService
from app.services.tenant_service import TenantService
from app.services.unit_service import UnitService


class BillNotFoundError(Exception):
    """Raised when a bill does not exist within the given building."""


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _due_date_for(period: str, due_day: int) -> str | None:
    """Build an ISO due date from a 'YYYY-MM' period and a day-of-month."""
    try:
        year, month = (int(p) for p in period.split("-"))
    except (ValueError, AttributeError):
        return None
    # Clamp day to a safe value for any month.
    day = min(max(due_day, 1), 28)
    return date(year, month, day).isoformat()


def _status_for(amount: int, paid_amount: int, due_date: str | None) -> str:
    """Derive a bill status from amounts and the due date."""
    if amount > 0 and paid_amount >= amount:
        return "paid"
    if paid_amount > 0:
        return "partial"
    # Unpaid — flag overdue once the due date has passed.
    if due_date and due_date < _today_iso():
        return "overdue"
    return "unpaid"


class BillService:
    def __init__(
        self,
        repository: BillRepository,
        building_service: BuildingService,
        lease_service: LeaseService,
        tenant_service: TenantService,
        unit_service: UnitService,
    ) -> None:
        self._repo = repository
        self._buildings = building_service
        self._leases = lease_service
        self._tenants = tenant_service
        self._units = unit_service

    async def _assert_building(self, owner: str, building_id: str) -> None:
        await self._buildings.get(owner, building_id)

    async def _labels(
        self, owner: str, building_id: str, tenant_id: str | None, unit_id: str | None
    ) -> tuple[str | None, str | None]:
        """Resolve denormalized tenant name + unit label for display."""
        tenant_name = None
        unit_label = None
        if tenant_id:
            try:
                tenant_name = (await self._tenants.get(owner, building_id, tenant_id)).name
            except Exception:  # noqa: BLE001 - tolerate dangling references
                pass
        if unit_id:
            try:
                unit_label = (await self._units.get(owner, building_id, unit_id)).label
            except Exception:  # noqa: BLE001
                pass
        return tenant_name, unit_label

    def _to_model(self, doc: dict) -> Bill:
        # Recompute the live status (so 'overdue' reflects the current date).
        doc["paid_amount"] = sum(p.get("amount", 0) for p in doc.get("payments", []))
        doc["status"] = _status_for(
            int(doc.get("amount", 0)), int(doc["paid_amount"]), doc.get("due_date")
        )
        return Bill(**doc)

    async def create(self, owner: str, building_id: str, payload: BillCreate) -> Bill:
        await self._assert_building(owner, building_id)
        tenant_name, unit_label = await self._labels(
            owner, building_id, payload.tenant_id, payload.unit_id
        )
        now = datetime.now(timezone.utc)
        document = {
            "id": str(uuid.uuid4()),
            "building_id": building_id,
            "unit_id": payload.unit_id,
            "tenant_id": payload.tenant_id,
            "tenant_name": tenant_name,
            "unit_label": unit_label,
            "bill_type": payload.bill_type.value,
            "period": payload.period,
            "amount": payload.amount,
            "paid_amount": 0,
            "status": _status_for(payload.amount, 0, payload.due_date),
            "due_date": payload.due_date,
            "note": payload.note,
            "payments": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        created = await self._repo.create(document)
        return self._to_model(created)

    async def get(self, owner: str, building_id: str, bill_id: str) -> Bill:
        await self._assert_building(owner, building_id)
        doc = await self._repo.get(bill_id, building_id)
        if doc is None:
            raise BillNotFoundError(bill_id)
        return self._to_model(doc)

    async def list(
        self,
        owner: str,
        building_id: str,
        period: str | None,
        status: str | None,
        bill_type: str | None,
        tenant_id: str | None,
        limit: int,
        offset: int,
    ) -> list[Bill]:
        await self._assert_building(owner, building_id)
        docs = await self._repo.list_for_building(
            building_id,
            period=period,
            bill_type=bill_type,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )
        bills = [self._to_model(d) for d in docs]
        # Status is computed live, so filter here rather than in the query.
        if status is not None:
            bills = [b for b in bills if b.status.value == status]
        bills.sort(key=lambda b: (b.period, b.bill_type.value), reverse=True)
        return bills

    async def update(
        self, owner: str, building_id: str, bill_id: str, payload: BillUpdate
    ) -> Bill:
        await self._assert_building(owner, building_id)
        doc = await self._repo.get(bill_id, building_id)
        if doc is None:
            raise BillNotFoundError(bill_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            doc[key] = value.value if hasattr(value, "value") else value
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = await self._repo.update(doc)
        return self._to_model(updated)

    async def record_payment(
        self, owner: str, building_id: str, bill_id: str, payload: PaymentCreate
    ) -> Bill:
        await self._assert_building(owner, building_id)
        doc = await self._repo.get(bill_id, building_id)
        if doc is None:
            raise BillNotFoundError(bill_id)
        now = datetime.now(timezone.utc)
        payment = {
            "id": str(uuid.uuid4()),
            "amount": payload.amount,
            "method": payload.method,
            "note": payload.note,
            "paid_on": payload.paid_on or now.date().isoformat(),
            "created_at": now.isoformat(),
        }
        doc.setdefault("payments", []).append(payment)
        doc["paid_amount"] = sum(p.get("amount", 0) for p in doc["payments"])
        doc["status"] = _status_for(int(doc.get("amount", 0)), doc["paid_amount"], doc.get("due_date"))
        doc["updated_at"] = now.isoformat()
        updated = await self._repo.update(doc)
        return self._to_model(updated)

    async def set_rent_status(
        self, owner: str, building_id: str, tenant_id: str, period: str, paid: bool
    ) -> Bill | None:
        """One-click toggle of a tenant's rent for a month (rent tracker grid).

        Marking paid creates the rent bill from the active lease if none exists,
        then settles it in full. Un-marking clears the recorded payments.
        """
        await self._assert_building(owner, building_id)
        existing = await self._repo.list_for_building(building_id, period=period)
        doc = next(
            (
                b for b in existing
                if b.get("tenant_id") == tenant_id and b.get("bill_type") == "rent"
            ),
            None,
        )

        if doc is None:
            if not paid:
                return None  # nothing recorded to clear
            leases = await self._leases.list(owner, building_id, limit=1000, offset=0)
            lease = next(
                (
                    l for l in leases
                    if l.tenant_id == tenant_id and l.status.value == "active"
                ),
                None,
            )
            bill = await self.create(
                owner,
                building_id,
                BillCreate(
                    unit_id=lease.unit_id if lease else None,
                    tenant_id=tenant_id,
                    bill_type=BillType.RENT,
                    period=period,
                    amount=lease.monthly_rent if lease else 0,
                    due_date=_due_date_for(period, lease.rent_due_day) if lease else None,
                ),
            )
            doc = await self._repo.get(bill.id, building_id)
            if doc is None:  # pragma: no cover - just-created
                return bill

        now = datetime.now(timezone.utc)
        if paid:
            amount = int(doc.get("amount", 0))
            doc["payments"] = [
                {
                    "id": str(uuid.uuid4()),
                    "amount": amount,
                    "method": "manual",
                    "note": "Marked paid",
                    "paid_on": now.date().isoformat(),
                    "created_at": now.isoformat(),
                }
            ]
            doc["paid_amount"] = amount
        else:
            doc["payments"] = []
            doc["paid_amount"] = 0
        doc["status"] = _status_for(int(doc.get("amount", 0)), doc["paid_amount"], doc.get("due_date"))
        doc["updated_at"] = now.isoformat()
        updated = await self._repo.update(doc)
        return self._to_model(updated)

    async def delete(self, owner: str, building_id: str, bill_id: str) -> None:
        await self._assert_building(owner, building_id)
        deleted = await self._repo.delete(bill_id, building_id)
        if not deleted:
            raise BillNotFoundError(bill_id)

    async def generate_monthly(
        self, owner: str, building_id: str, payload: GenerateBillsRequest
    ) -> list[Bill]:
        """Create rent (+ optional utility) bills for every active lease in a month.

        Idempotent per (lease, type, period): a bill that already exists for the
        same tenant/type/period is skipped so re-running doesn't duplicate.
        """
        await self._assert_building(owner, building_id)
        existing = await self._repo.list_for_building(building_id, period=payload.period)

        def already(tenant_id: str | None, bill_type: str) -> bool:
            return any(
                b.get("tenant_id") == tenant_id and b.get("bill_type") == bill_type
                for b in existing
            )

        extras: list[tuple[str, int]] = []
        if payload.include_water and payload.water_amount > 0:
            extras.append(("water", payload.water_amount))
        if payload.include_electricity and payload.electricity_amount > 0:
            extras.append(("electricity", payload.electricity_amount))
        if payload.include_maintenance and payload.maintenance_amount > 0:
            extras.append(("maintenance", payload.maintenance_amount))

        created: list[Bill] = []
        leases = await self._leases.list(owner, building_id, limit=1000, offset=0)
        for lease in leases:
            if lease.status.value != "active":
                continue
            due = _due_date_for(payload.period, lease.rent_due_day)
            charges: list[tuple[str, int, str | None]] = [("rent", lease.monthly_rent, due)]
            for bill_type, amount in extras:
                charges.append((bill_type, amount, due))
            for bill_type, amount, due_date in charges:
                if amount <= 0 or already(lease.tenant_id, bill_type):
                    continue
                bill = await self.create(
                    owner,
                    building_id,
                    BillCreate(
                        unit_id=lease.unit_id,
                        tenant_id=lease.tenant_id,
                        bill_type=bill_type,  # type: ignore[arg-type]
                        period=payload.period,
                        amount=amount,
                        due_date=due_date,
                    ),
                )
                created.append(bill)
        return created


__all__ = ["BillService", "BillNotFoundError"]
