"""Aggregated KPIs for the landlord dashboard."""
from __future__ import annotations

from datetime import datetime, timezone

from app.services.bill_service import BillService
from app.services.building_service import BuildingService
from app.services.tenant_service import TenantService
from app.services.unit_service import UnitService


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


class DashboardService:
    def __init__(
        self,
        building_service: BuildingService,
        unit_service: UnitService,
        tenant_service: TenantService,
        bill_service: BillService,
    ) -> None:
        self._buildings = building_service
        self._units = unit_service
        self._tenants = tenant_service
        self._bills = bill_service

    async def summary(self, owner: str, period: str | None = None) -> dict:
        period = period or _current_period()
        buildings = await self._buildings.list(owner, limit=1000, offset=0)

        total_units = 0
        occupied_units = 0
        active_tenants = 0
        expected = collected = 0
        by_type: dict[str, int] = {}
        overdue: list[dict] = []
        recent_payments: list[dict] = []
        per_building: list[dict] = []

        for b in buildings:
            units = await self._units.list(owner, b.id, limit=1000, offset=0)
            tenants = await self._tenants.list(owner, b.id, limit=1000, offset=0)
            bills = await self._bills.list(
                owner, b.id, period=period, status=None, bill_type=None,
                tenant_id=None, limit=2000, offset=0,
            )

            total_units += len(units)
            occupied_units += sum(1 for u in units if u.status.value == "occupied")
            active_tenants += sum(1 for t in tenants if t.status.value == "active")

            b_expected = sum(bill.amount for bill in bills)
            b_collected = sum(bill.paid_amount for bill in bills)
            expected += b_expected
            collected += b_collected
            per_building.append(
                {
                    "building_id": b.id,
                    "name": b.name,
                    "units": len(units),
                    "expected": b_expected,
                    "collected": b_collected,
                    "outstanding": b_expected - b_collected,
                }
            )

            for bill in bills:
                by_type[bill.bill_type.value] = (
                    by_type.get(bill.bill_type.value, 0) + bill.amount
                )
                if bill.status.value == "overdue":
                    overdue.append(
                        {
                            "id": bill.id,
                            "building_id": b.id,
                            "building_name": b.name,
                            "tenant_name": bill.tenant_name,
                            "unit_label": bill.unit_label,
                            "bill_type": bill.bill_type.value,
                            "period": bill.period,
                            "amount": bill.amount,
                            "paid_amount": bill.paid_amount,
                            "due_date": bill.due_date,
                        }
                    )
                for p in bill.payments:
                    recent_payments.append(
                        {
                            "bill_id": bill.id,
                            "building_name": b.name,
                            "tenant_name": bill.tenant_name,
                            "bill_type": bill.bill_type.value,
                            "amount": p.amount,
                            "paid_on": p.paid_on,
                        }
                    )

        recent_payments.sort(key=lambda p: p.get("paid_on") or "", reverse=True)
        overdue.sort(key=lambda o: o.get("due_date") or "")
        occupancy = round(occupied_units / total_units * 100) if total_units else 0

        return {
            "period": period,
            "buildings": len(buildings),
            "units": total_units,
            "occupied_units": occupied_units,
            "occupancy_pct": occupancy,
            "active_tenants": active_tenants,
            "expected": expected,
            "collected": collected,
            "outstanding": expected - collected,
            "by_type": [{"type": k, "amount": v} for k, v in by_type.items()],
            "per_building": per_building,
            "overdue": overdue[:20],
            "recent_payments": recent_payments[:10],
        }


__all__ = ["DashboardService"]
