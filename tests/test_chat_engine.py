"""Unit tests for the rule-based chat engine using an in-memory fake client."""
from __future__ import annotations

import uuid
from typing import Any

from app.chat.chat_engine import handle


class FakeClient:
    """Mimics chat.api_client.ApiClient with plain dicts — no network."""

    def __init__(self) -> None:
        self.buildings: dict[str, dict[str, Any]] = {}
        self.units: dict[str, dict[str, Any]] = {}
        self.tenants: dict[str, dict[str, Any]] = {}
        self.bills: dict[str, dict[str, Any]] = {}

    # --- builders used by tests ---
    def add_building(self, name: str, city: str | None = None) -> dict[str, Any]:
        bid = str(uuid.uuid4())
        b = {"id": bid, "name": name, "city": city}
        self.buildings[bid] = b
        return b

    def add_unit(self, building_id: str, label: str, status: str = "occupied") -> dict[str, Any]:
        uid = str(uuid.uuid4())
        u = {"id": uid, "building_id": building_id, "label": label, "status": status}
        self.units[uid] = u
        return u

    def add_tenant(self, building_id: str, name: str, phone: str | None = None) -> dict[str, Any]:
        tid = str(uuid.uuid4())
        t = {"id": tid, "building_id": building_id, "name": name, "phone": phone}
        self.tenants[tid] = t
        return t

    def add_bill(self, building_id: str, **kw: Any) -> dict[str, Any]:
        bid = str(uuid.uuid4())
        bill = {
            "id": bid,
            "building_id": building_id,
            "bill_type": kw.get("bill_type", "rent"),
            "period": kw.get("period", "2026-06"),
            "amount": kw.get("amount", 10000),
            "paid_amount": kw.get("paid_amount", 0),
            "status": kw.get("status", "unpaid"),
            "tenant_name": kw.get("tenant_name"),
            "unit_label": kw.get("unit_label"),
        }
        self.bills[bid] = bill
        return bill

    # --- ApiClient surface ---
    def list_buildings(self) -> list[dict[str, Any]]:
        return list(self.buildings.values())

    def list_units(self, building_id: str) -> list[dict[str, Any]]:
        return [u for u in self.units.values() if u["building_id"] == building_id]

    def list_tenants(self, building_id: str) -> list[dict[str, Any]]:
        return [t for t in self.tenants.values() if t["building_id"] == building_id]

    def list_bills(self, building_id, period=None, status=None, bill_type=None):
        out = [b for b in self.bills.values() if b["building_id"] == building_id]
        if period:
            out = [b for b in out if b["period"] == period]
        if status:
            out = [b for b in out if b["status"] == status]
        if bill_type:
            out = [b for b in out if b["bill_type"] == bill_type]
        return out

    def dashboard(self, period: str | None = None) -> dict[str, Any]:
        bills = list(self.bills.values())
        if period:
            bills = [b for b in bills if b["period"] == period]
        expected = sum(b["amount"] for b in bills)
        collected = sum(b["paid_amount"] for b in bills)
        units = list(self.units.values())
        occ = sum(1 for u in units if u["status"] == "occupied")
        return {
            "period": period or "2026-06",
            "buildings": len(self.buildings),
            "units": len(units),
            "occupied_units": occ,
            "occupancy_pct": round(occ / len(units) * 100) if units else 0,
            "active_tenants": len(self.tenants),
            "expected": expected,
            "collected": collected,
            "outstanding": expected - collected,
            "overdue": [b for b in bills if b["status"] == "overdue"],
        }


def test_help_and_greeting() -> None:
    client = FakeClient()
    assert "manage your rentals" in handle(client, "help")
    assert "rental assistant" in handle(client, "hello").lower()


def test_list_buildings() -> None:
    client = FakeClient()
    b = client.add_building("Lakeview", city="Bengaluru")
    client.add_unit(b["id"], "A-101", status="occupied")
    reply = handle(client, "list my buildings")
    assert "Lakeview" in reply
    assert "1/1 units occupied" in reply


def test_tenants_in_building() -> None:
    client = FakeClient()
    b = client.add_building("Green Meadows")
    client.add_tenant(b["id"], "Anjali Verma", phone="+91 90210 33445")
    reply = handle(client, "show tenants in Green Meadows")
    assert "Anjali Verma" in reply


def test_overdue_bills() -> None:
    client = FakeClient()
    b = client.add_building("Sunrise")
    client.add_bill(b["id"], status="overdue", amount=20000, tenant_name="Rohit")
    client.add_bill(b["id"], status="paid", amount=15000, paid_amount=15000, tenant_name="Priya")
    reply = handle(client, "who hasn't paid rent?")
    assert "Rohit" in reply
    assert "₹20,000" in reply
    assert "Priya" not in reply


def test_summary() -> None:
    client = FakeClient()
    b = client.add_building("Park")
    client.add_unit(b["id"], "1", status="occupied")
    client.add_bill(b["id"], amount=10000, paid_amount=4000, status="partial")
    reply = handle(client, "this month's summary")
    assert "Expected ₹10,000" in reply
    assert "outstanding ₹6,000" in reply
