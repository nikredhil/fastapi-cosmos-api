"""Tenant schemas. A tenant belongs to a building and (optionally) occupies a unit."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain.enums import TenantStatus


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=0, le=120, description="Tenant age in years")
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=200)
    permanent_address: str | None = Field(
        default=None, max_length=500, description="Tenant's permanent/home address"
    )
    unit_id: str | None = Field(default=None, description="Unit this tenant occupies")
    move_in_date: str | None = Field(default=None, description="ISO date, e.g. 2026-06-01")
    deposit: int = Field(default=0, ge=0, description="Security deposit in INR")
    monthly_rent: int = Field(default=0, ge=0, description="Current monthly rent in INR")
    lease_months: int | None = Field(
        default=None, ge=1, le=600, description="Contract length in months"
    )
    rent_increase_pct: float | None = Field(
        default=None, ge=0, le=100, description="Rent increase % applied on renewal"
    )
    avatar_color: str | None = Field(default=None, description="Hex color, e.g. #2563eb")


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=0, le=120)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=200)
    permanent_address: str | None = Field(default=None, max_length=500)
    unit_id: str | None = None
    move_in_date: str | None = None
    deposit: int | None = Field(default=None, ge=0)
    monthly_rent: int | None = Field(default=None, ge=0)
    lease_months: int | None = Field(default=None, ge=1, le=600)
    rent_increase_pct: float | None = Field(default=None, ge=0, le=100)
    status: TenantStatus | None = None
    avatar_color: str | None = None
    aadhaar_image_id: str | None = Field(default=None, description="Uploaded Aadhaar card image id")


class Tenant(BaseModel):
    id: str
    building_id: str = Field(description="Parent building (partition key)")
    name: str
    age: int | None = None
    phone: str | None = None
    email: str | None = None
    permanent_address: str | None = None
    unit_id: str | None = None
    move_in_date: str | None = None
    deposit: int = 0
    monthly_rent: int = 0
    lease_months: int | None = None
    rent_increase_pct: float | None = None
    status: TenantStatus = TenantStatus.ACTIVE
    avatar_color: str | None = None
    aadhaar_image_id: str | None = None
    created_at: datetime
    updated_at: datetime
