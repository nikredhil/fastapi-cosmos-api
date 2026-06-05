"""Thin HTTP client the chat assistant uses to call the API as the signed-in user."""
from __future__ import annotations

from typing import Any

import httpx


class ApiError(Exception):
    """Raised when the API returns a non-success status."""


class ApiClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token

    @property
    def token(self) -> str | None:
        return self._token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        resp = httpx.request(
            method, f"{self.base_url}{path}", headers=self._headers(), timeout=15.0, **kwargs
        )
        if resp.status_code >= 400:
            raise ApiError(f"{resp.status_code}: {resp.text}")
        return resp

    # --- buildings ---
    def list_buildings(self) -> list[dict[str, Any]]:
        return self._request("GET", "/buildings").json()["items"]

    def create_building(self, name: str, address: str | None = None) -> dict[str, Any]:
        body = {"name": name, "address": address}
        return self._request("POST", "/buildings", json=body).json()

    # --- units & tenants ---
    def list_units(self, building_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/buildings/{building_id}/units").json()["items"]

    def list_tenants(self, building_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/buildings/{building_id}/tenants").json()["items"]

    # --- bills ---
    def list_bills(
        self,
        building_id: str,
        period: str | None = None,
        status: str | None = None,
        bill_type: str | None = None,
    ) -> list[dict[str, Any]]:
        params = {}
        if period:
            params["period"] = period
        if status:
            params["status"] = status
        if bill_type:
            params["bill_type"] = bill_type
        return self._request(
            "GET", f"/buildings/{building_id}/bills", params=params or None
        ).json()["items"]

    # --- dashboard ---
    def dashboard(self, period: str | None = None) -> dict[str, Any]:
        params = {"period": period} if period else None
        return self._request("GET", "/dashboard", params=params).json()
