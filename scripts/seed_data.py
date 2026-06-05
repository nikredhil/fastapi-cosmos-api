"""Seed the API with sample buildings, units, tenants, leases, and bills.

The API authenticates with a bearer token. The easiest path locally is a local
account: register/sign in on the web app, copy the bearer token from any API
request (DevTools → Network → Authorization header), then:

    API_TOKEN="<token>" python -m scripts.seed_data
    API_BASE=http://localhost:8000 API_TOKEN="<token>" python -m scripts.seed_data
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN")

PERIOD = datetime.now(timezone.utc).strftime("%Y-%m")

# Per building: units (label, floor, bedrooms, rent) and tenants
# (name, phone, unit-index, deposit). Tenants are placed into units by index.
SAMPLE = {
    "Lakeview Apartments": {
        "city": "Bengaluru",
        "address": "12 Lakeview Rd, Indiranagar",
        "units": [
            ("A-101", 1, 2, 24000),
            ("A-102", 1, 1, 16000),
            ("B-201", 2, 3, 32000),
        ],
        "tenants": [
            ("Rohit Sharma", "+91 98450 11223", 0, 48000),
            ("Priya Nair", "+91 99860 44556", 1, 32000),
            ("Imran Khan", "+91 97400 77889", 2, 64000),
        ],
    },
    "Green Meadows": {
        "city": "Pune",
        "address": "45 MG Road, Kothrud",
        "units": [
            ("101", 1, 2, 18000),
            ("102", 1, 2, 18500),
        ],
        "tenants": [
            ("Anjali Verma", "+91 90210 33445", 0, 36000),
            ("Karthik Rao", "+91 99000 22113", 1, 37000),
        ],
    },
}


def main() -> None:
    if not API_TOKEN:
        sys.exit(
            "API_TOKEN is required. Sign in to the web app, copy the bearer token from a "
            "/buildings request (DevTools → Network), and re-run with API_TOKEN=<token>."
        )
    with httpx.Client(base_url=API_BASE, timeout=15.0) as client:
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        n_b = n_u = n_t = n_l = n_bills = 0

        for name, spec in SAMPLE.items():
            bid = client.post(
                "/buildings",
                json={"name": name, "city": spec["city"], "address": spec["address"]},
                headers=headers,
            ).json()["id"]
            n_b += 1

            unit_ids: list[str] = []
            for label, floor, beds, rent in spec["units"]:
                uid = client.post(
                    f"/buildings/{bid}/units",
                    json={"label": label, "floor": floor, "bedrooms": beds, "default_rent": rent},
                    headers=headers,
                ).json()["id"]
                unit_ids.append(uid)
                n_u += 1

            for tenant_name, phone, unit_idx, deposit in spec["tenants"]:
                uid = unit_ids[unit_idx]
                tenant = client.post(
                    f"/buildings/{bid}/tenants",
                    json={
                        "name": tenant_name,
                        "phone": phone,
                        "unit_id": uid,
                        "deposit": deposit,
                        "move_in_date": "2026-01-01",
                    },
                    headers=headers,
                ).json()
                n_t += 1
                rent = spec["units"][unit_idx][3]
                client.post(
                    f"/buildings/{bid}/leases",
                    json={
                        "unit_id": uid,
                        "tenant_id": tenant["id"],
                        "monthly_rent": rent,
                        "deposit": deposit,
                        "rent_due_day": 5,
                        "start_date": "2026-01-01",
                    },
                    headers=headers,
                )
                n_l += 1

            # Generate this month's rent + utilities, then mark a few as paid.
            generated = client.post(
                f"/buildings/{bid}/bills/generate",
                json={
                    "period": PERIOD,
                    "include_water": True,
                    "include_electricity": True,
                    "water_amount": 600,
                    "electricity_amount": 1800,
                },
                headers=headers,
            ).json()["items"]
            n_bills += len(generated)

            # Pay the first generated rent bill fully, leave others outstanding.
            for bill in generated:
                if bill["bill_type"] == "rent":
                    client.post(
                        f"/buildings/{bid}/bills/{bill['id']}/payments",
                        json={"amount": bill["amount"], "method": "upi"},
                        headers=headers,
                    )
                    break

        print(
            f"Seeded {n_b} buildings, {n_u} units, {n_t} tenants, {n_l} leases, "
            f"and {n_bills} bills for {PERIOD} at {API_BASE}"
        )


if __name__ == "__main__":
    main()
