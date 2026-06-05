"""Tenant schemas. A tenant belongs to a building and (optionally) occupies a unit."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain.enums import TenantStatus


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=200)
    unit_id: str | None = Field(default=None, description="Unit this tenant occupies")
    move_in_date: str | None = Field(default=None, description="ISO date, e.g. 2026-06-01")
    deposit: int = Field(default=0, ge=0, description="Security deposit in INR")
    avatar_color: str | None = Field(default=None, description="Hex color, e.g. #2563eb")


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=200)
    unit_id: str | None = None
    move_in_date: str | None = None
    deposit: int | None = Field(default=None, ge=0)
    status: TenantStatus | None = None
    avatar_color: str | None = None
    aadhaar_image_id: str | None = Field(default=None, description="Uploaded Aadhaar card image id")


class Tenant(BaseModel):
    id: str
    building_id: str = Field(description="Parent building (partition key)")
    name: str
    phone: str | None = None
    email: str | None = None
    unit_id: str | None = None
    move_in_date: str | None = None
    deposit: int = 0
    status: TenantStatus = TenantStatus.ACTIVE
    avatar_color: str | None = None
    aadhaar_image_id: str | None = None
    created_at: datetime
    updated_at: datetime
