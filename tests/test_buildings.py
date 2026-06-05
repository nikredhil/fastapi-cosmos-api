"""Integration tests for buildings, units, tenants, and dashboard."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_building_crud_and_isolation(client, auth_headers) -> None:
    # Create a building.
    resp = await client.post(
        "/buildings", json={"name": "Lakeview", "city": "Bengaluru"}, headers=auth_headers
    )
    assert resp.status_code == 201
    building = resp.json()
    assert building["name"] == "Lakeview"
    bid = building["id"]

    # Listed for the owner.
    listed = await client.get("/buildings", headers=auth_headers)
    assert listed.status_code == 200
    assert any(b["id"] == bid for b in listed.json()["items"])

    # A different user can't see it.
    other = await client.get("/buildings", headers={"Authorization": "Bearer bob"})
    assert all(b["id"] != bid for b in other.json()["items"])

    # Delete.
    deleted = await client.delete(f"/buildings/{bid}", headers=auth_headers)
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_unit_and_tenant_occupancy(client, auth_headers) -> None:
    bid = (await client.post("/buildings", json={"name": "Green"}, headers=auth_headers)).json()["id"]

    unit = (
        await client.post(
            f"/buildings/{bid}/units",
            json={"label": "101", "default_rent": 15000},
            headers=auth_headers,
        )
    ).json()
    assert unit["status"] == "vacant"

    tenant = (
        await client.post(
            f"/buildings/{bid}/tenants",
            json={"name": "Asha", "unit_id": unit["id"], "deposit": 30000},
            headers=auth_headers,
        )
    ).json()
    assert tenant["status"] == "active"
    assert tenant["avatar_color"]  # auto-assigned

    # Assigning the tenant marks the unit occupied.
    units = (await client.get(f"/buildings/{bid}/units", headers=auth_headers)).json()["items"]
    assert units[0]["status"] == "occupied"


@pytest.mark.asyncio
async def test_dashboard_reflects_data(client, auth_headers) -> None:
    bid = (await client.post("/buildings", json={"name": "Park"}, headers=auth_headers)).json()["id"]
    unit = (
        await client.post(
            f"/buildings/{bid}/units", json={"label": "1", "default_rent": 10000}, headers=auth_headers
        )
    ).json()
    await client.post(
        f"/buildings/{bid}/tenants",
        json={"name": "Dev", "unit_id": unit["id"]},
        headers=auth_headers,
    )

    d = (await client.get("/dashboard", headers=auth_headers)).json()
    assert d["buildings"] == 1
    assert d["units"] == 1
    assert d["occupied_units"] == 1
    assert d["occupancy_pct"] == 100
