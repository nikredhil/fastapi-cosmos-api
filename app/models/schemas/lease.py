"""Lease/contract schemas. A lease ties a tenant to a unit for a term."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain.enums import LeaseStatus


class LeaseCreate(BaseModel):
    unit_id: str
    tenant_id: str
    start_date: str | None = Field(default=None, description="ISO date")
    end_date: str | None = Field(default=None, description="ISO date")
    monthly_rent: int = Field(default=0, ge=0, description="Monthly rent in INR")
    deposit: int = Field(default=0, ge=0, description="Security deposit in INR")
    rent_due_day: int = Field(default=5, ge=1, le=31, description="Day of month rent is due")
    lease_months: int | None = Field(
        default=None, ge=1, le=600, description="Contract length in months"
    )
    rent_increase_pct: float | None = Field(
        default=None, ge=0, le=100, description="Rent increase % applied on renewal"
    )
    terms: str | None = Field(default=None, max_length=8000)
    contract_image_id: str | None = Field(
        default=None, description="Id of an uploaded contract image, if any"
    )
    parsed: bool = Field(default=False, description="Was this lease prefilled from a parsed photo?")


class LeaseUpdate(BaseModel):
    unit_id: str | None = None
    tenant_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    monthly_rent: int | None = Field(default=None, ge=0)
    deposit: int | None = Field(default=None, ge=0)
    rent_due_day: int | None = Field(default=None, ge=1, le=31)
    lease_months: int | None = Field(default=None, ge=1, le=600)
    rent_increase_pct: float | None = Field(default=None, ge=0, le=100)
    terms: str | None = Field(default=None, max_length=8000)
    contract_image_id: str | None = None
    status: LeaseStatus | None = None


class Lease(BaseModel):
    id: str
    building_id: str = Field(description="Parent building (partition key)")
    unit_id: str
    tenant_id: str
    start_date: str | None = None
    end_date: str | None = None
    monthly_rent: int = 0
    deposit: int = 0
    rent_due_day: int = 5
    lease_months: int | None = None
    rent_increase_pct: float | None = None
    terms: str | None = None
    contract_image_id: str | None = None
    parsed: bool = False
    status: LeaseStatus = LeaseStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
