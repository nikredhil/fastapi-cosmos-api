"""Tests for image delete, the move-in date, and fixed 5%/11-month renewals."""
from __future__ import annotations

import io

import pytest

PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
    b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


async def _building(client, headers, name="Tower"):
    return (await client.post("/buildings", json={"name": name}, headers=headers)).json()["id"]


@pytest.mark.asyncio
async def test_upload_then_delete_image(client, auth_headers) -> None:
    bid = await _building(client, auth_headers)

    up = await client.post(
        f"/buildings/{bid}/contracts/upload",
        files={"file": ("page.png", io.BytesIO(PNG_1x1), "image/png")},
        headers=auth_headers,
    )
    assert up.status_code == 201
    image_id = up.json()["image_id"]

    url = f"/buildings/{bid}/contracts/{image_id}"
    # It can be fetched...
    assert (await client.get(url, headers=auth_headers)).status_code == 200

    # ...deleted...
    deleted = await client.delete(url, headers=auth_headers)
    assert deleted.status_code == 204

    # ...and is then gone.
    assert (await client.get(url, headers=auth_headers)).status_code == 404


@pytest.mark.asyncio
async def test_move_in_date_round_trips(client, auth_headers) -> None:
    bid = await _building(client, auth_headers)
    tenant = (
        await client.post(
            f"/buildings/{bid}/tenants", json={"name": "Ravi"}, headers=auth_headers
        )
    ).json()

    patched = await client.patch(
        f"/buildings/{bid}/tenants/{tenant['id']}",
        json={"move_in_date": "2025-01-15"},
        headers=auth_headers,
    )
    assert patched.status_code == 200
    assert patched.json()["move_in_date"] == "2025-01-15"


@pytest.mark.asyncio
async def test_renewal_is_fixed_5pct_even_with_higher_override(client, auth_headers) -> None:
    bid = await _building(client, auth_headers)
    unit = (
        await client.post(
            f"/buildings/{bid}/units",
            json={"label": "1", "default_rent": 25000},
            headers=auth_headers,
        )
    ).json()
    # Tenant carries a 6% override and a non-11-month term — both must be ignored.
    tenant = (
        await client.post(
            f"/buildings/{bid}/tenants",
            json={
                "name": "Yash",
                "unit_id": unit["id"],
                "monthly_rent": 25000,
                "move_in_date": "2025-01-01",
                "rent_increase_pct": 6,
                "lease_months": 12,
            },
            headers=auth_headers,
        )
    ).json()
    assert tenant["id"]

    d = (await client.get("/dashboard", headers=auth_headers)).json()
    inc = next(r for r in d["rent_increases"] if r["tenant_name"] == "Yash")
    assert inc["increase_pct"] == 5.0
    assert inc["new_rent"] == 26250  # 25000 * 1.05, not 1.06
    assert inc["renewal_date"] == "2025-12-01"  # +11 months, not +12


@pytest.mark.asyncio
async def test_renewal_falls_back_to_lease_start_date(client, auth_headers) -> None:
    bid = await _building(client, auth_headers)
    unit = (
        await client.post(
            f"/buildings/{bid}/units",
            json={"label": "2", "default_rent": 20000},
            headers=auth_headers,
        )
    ).json()
    # No move_in_date on the tenant — the dashboard must anchor on the lease.
    tenant = (
        await client.post(
            f"/buildings/{bid}/tenants",
            json={"name": "Noah", "unit_id": unit["id"], "monthly_rent": 20000},
            headers=auth_headers,
        )
    ).json()
    await client.post(
        f"/buildings/{bid}/leases",
        json={
            "unit_id": unit["id"],
            "tenant_id": tenant["id"],
            "monthly_rent": 20000,
            "start_date": "2025-03-01",
        },
        headers=auth_headers,
    )

    d = (await client.get("/dashboard", headers=auth_headers)).json()
    inc = next(r for r in d["rent_increases"] if r["tenant_name"] == "Noah")
    assert inc["renewal_date"] == "2026-02-01"  # 2025-03-01 + 11 months
    assert inc["increase_pct"] == 5.0
