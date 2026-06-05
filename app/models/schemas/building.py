"""Building request/response schemas. A building is owned by one landlord."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BuildingCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


class BuildingUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


class Building(BaseModel):
    id: str
    owner: str = Field(description="User id of the landlord who owns this building (partition key)")
    name: str
    address: str | None = None
    city: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
