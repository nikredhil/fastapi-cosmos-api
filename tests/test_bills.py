"""Integration tests for bills: generation, payments, status transitions."""
from __future__ import annotations

import pytest

# A far-future month so generated bills' due dates are always ahead of "today"
# (keeps the unpaid/partial assertions stable regardless of when tests run).
PERIOD = "2099-12"


async def _building_with_lease(client, headers, rent=20000):
    bid = (await client.post("/buildings", json={"name": "Sunrise"}, headers=headers)).json()["id"]
    unit = (
        await client.post(
            f"/buildings/{bid}/units", json={"label": "A1", "default_rent": rent}, headers=headers
        )
    ).json()
    tenant = (
        await client.post(
            f"/buildings/{bid}/tenants", json={"name": "Meera", "unit_id": unit["id"]}, headers=headers
        )
    ).json()
    await client.post(
        f"/buildings/{bid}/leases",
        json={"unit_id": unit["id"], "tenant_id": tenant["id"], "monthly_rent": rent, "rent_due_day": 5},
        headers=headers,
    )
    return bid


@pytest.mark.asyncio
async def test_generate_is_idempotent(client, auth_headers) -> None:
    bid = await _building_with_lease(client, auth_headers)

    first = await client.post(
        f"/buildings/{bid}/bills/generate",
        json={"period": PERIOD, "include_water": True, "water_amount": 500},
        headers=auth_headers,
    )
    assert first.status_code == 201
    items = first.json()["items"]
    assert len(items) == 2  # rent + water
    assert {b["bill_type"] for b in items} == {"rent", "water"}
    assert any(b["amount"] == 20000 for b in items)

    # Re-running doesn't duplicate.
    again = await client.post(
        f"/buildings/{bid}/bills/generate",
        json={"period": PERIOD, "include_water": True, "water_amount": 500},
        headers=auth_headers,
    )
    assert again.json()["items"] == []


@pytest.mark.asyncio
async def test_payment_marks_paid(client, auth_headers) -> None:
    bid = await _building_with_lease(client, auth_headers, rent=15000)
    bills = (
        await client.post(
            f"/buildings/{bid}/bills/generate", json={"period": PERIOD}, headers=auth_headers
        )
    ).json()["items"]
    rent_bill = next(b for b in bills if b["bill_type"] == "rent")
    assert rent_bill["status"] == "unpaid"

    # Partial payment → partial.
    partial = await client.post(
        f"/buildings/{bid}/bills/{rent_bill['id']}/payments",
        json={"amount": 5000, "method": "cash"},
        headers=auth_headers,
    )
    assert partial.json()["status"] == "partial"
    assert partial.json()["paid_amount"] == 5000

    # Pay the rest → paid.
    full = await client.post(
        f"/buildings/{bid}/bills/{rent_bill['id']}/payments",
        json={"amount": 10000, "method": "upi"},
        headers=auth_headers,
    )
    assert full.json()["status"] == "paid"
    assert full.json()["paid_amount"] == 15000


@pytest.mark.asyncio
async def test_generate_bills_tenant_without_lease(client, auth_headers) -> None:
    # A manually added tenant (rent set, no lease) must still be billed.
    bid = (
        await client.post("/buildings", json={"name": "Manual"}, headers=auth_headers)
    ).json()["id"]
    unit = (
        await client.post(
            f"/buildings/{bid}/units",
            json={"label": "5", "default_rent": 12000},
            headers=auth_headers,
        )
    ).json()
    await client.post(
        f"/buildings/{bid}/tenants",
        json={"name": "Riya", "unit_id": unit["id"], "monthly_rent": 12000},
        headers=auth_headers,
    )

    items = (
        await client.post(
            f"/buildings/{bid}/bills/generate", json={"period": PERIOD}, headers=auth_headers
        )
    ).json()["items"]
    assert len(items) == 1
    assert items[0]["bill_type"] == "rent"
    assert items[0]["amount"] == 12000
    assert items[0]["tenant_name"] == "Riya"
    assert items[0]["unit_label"] == "5"


@pytest.mark.asyncio
async def test_generate_bills_no_duplicate_with_two_leases(client, auth_headers) -> None:
    # Two active leases for one tenant must not produce two rent bills.
    bid = (await client.post("/buildings", json={"name": "Dup"}, headers=auth_headers)).json()["id"]
    unit = (
        await client.post(
            f"/buildings/{bid}/units",
            json={"label": "9", "default_rent": 18000},
            headers=auth_headers,
        )
    ).json()
    tenant = (
        await client.post(
            f"/buildings/{bid}/tenants",
            json={"name": "Sam", "unit_id": unit["id"], "monthly_rent": 18000},
            headers=auth_headers,
        )
    ).json()
    for _ in range(2):
        await client.post(
            f"/buildings/{bid}/leases",
            json={"unit_id": unit["id"], "tenant_id": tenant["id"], "monthly_rent": 18000},
            headers=auth_headers,
        )

    items = (
        await client.post(
            f"/buildings/{bid}/bills/generate", json={"period": PERIOD}, headers=auth_headers
        )
    ).json()["items"]
    rent_bills = [b for b in items if b["bill_type"] == "rent"]
    assert len(rent_bills) == 1


@pytest.mark.asyncio
async def test_overdue_status_for_past_due_date(client, auth_headers) -> None:
    bid = (await client.post("/buildings", json={"name": "Old"}, headers=auth_headers)).json()["id"]
    bill = (
        await client.post(
            f"/buildings/{bid}/bills",
            json={"bill_type": "rent", "period": "2020-01", "amount": 9000, "due_date": "2020-01-05"},
            headers=auth_headers,
        )
    ).json()
    assert bill["status"] == "overdue"
