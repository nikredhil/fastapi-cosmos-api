"""Bill schemas — rent and utility charges, with embedded payment records."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain.enums import BillStatus, BillType


class Payment(BaseModel):
    id: str
    amount: int = Field(description="Amount paid in INR")
    method: str | None = None
    note: str | None = None
    paid_on: str | None = Field(default=None, description="ISO date the payment was made")
    created_at: datetime


class PaymentCreate(BaseModel):
    amount: int = Field(ge=1, description="Amount paid in INR")
    method: str | None = Field(default=None, max_length=60, description="cash / upi / bank, etc.")
    note: str | None = Field(default=None, max_length=500)
    paid_on: str | None = Field(default=None, description="ISO date; defaults to today")


class BillCreate(BaseModel):
    unit_id: str | None = None
    tenant_id: str | None = None
    bill_type: BillType = BillType.RENT
    period: str = Field(description="Billing month, e.g. 2026-06", max_length=7)
    amount: int = Field(ge=0, description="Amount due in INR")
    due_date: str | None = Field(default=None, description="ISO date")
    note: str | None = Field(default=None, max_length=500)


class BillUpdate(BaseModel):
    bill_type: BillType | None = None
    period: str | None = Field(default=None, max_length=7)
    amount: int | None = Field(default=None, ge=0)
    due_date: str | None = None
    status: BillStatus | None = None
    note: str | None = Field(default=None, max_length=500)


class GenerateBillsRequest(BaseModel):
    period: str = Field(description="Billing month to generate, e.g. 2026-06", max_length=7)
    include_water: bool = False
    include_electricity: bool = False
    include_maintenance: bool = False
    water_amount: int = Field(default=0, ge=0)
    electricity_amount: int = Field(default=0, ge=0)
    maintenance_amount: int = Field(default=0, ge=0)


class Bill(BaseModel):
    id: str
    building_id: str = Field(description="Parent building (partition key)")
    unit_id: str | None = None
    tenant_id: str | None = None
    tenant_name: str | None = Field(default=None, description="Denormalized for display")
    unit_label: str | None = Field(default=None, description="Denormalized for display")
    bill_type: BillType
    period: str
    amount: int = 0
    paid_amount: int = 0
    status: BillStatus = BillStatus.UNPAID
    due_date: str | None = None
    note: str | None = None
    payments: list[Payment] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
