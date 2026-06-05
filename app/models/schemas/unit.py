"""Unit (flat/apartment) schemas. Units belong to a building."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain.enums import UnitStatus


class UnitCreate(BaseModel):
    label: str = Field(min_length=1, max_length=60, description="Flat number, e.g. A-101")
    floor: int | None = Field(default=None, ge=-5, le=200)
    bedrooms: int | None = Field(default=None, ge=0, le=20)
    default_rent: int = Field(default=0, ge=0, description="Default monthly rent in INR")
    notes: str | None = Field(default=None, max_length=2000)


class UnitUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=60)
    floor: int | None = Field(default=None, ge=-5, le=200)
    bedrooms: int | None = Field(default=None, ge=0, le=20)
    default_rent: int | None = Field(default=None, ge=0)
    status: UnitStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)


class Unit(BaseModel):
    id: str
    building_id: str = Field(description="Parent building (partition key)")
    label: str
    floor: int | None = None
    bedrooms: int | None = None
    default_rent: int = 0
    status: UnitStatus = UnitStatus.VACANT
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
