"""Sprint request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain.enums import SprintStatus


class SprintCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    goal: str | None = Field(default=None, max_length=2000)
    start_date: str | None = Field(default=None, description="ISO date, e.g. 2026-06-05")
    end_date: str | None = None


class SprintUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    goal: str | None = Field(default=None, max_length=2000)
    start_date: str | None = None
    end_date: str | None = None
    status: SprintStatus | None = None


class Sprint(BaseModel):
    id: str
    project_id: str = Field(description="Parent project (partition key)")
    name: str
    goal: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: SprintStatus = SprintStatus.PLANNED
    created_at: datetime
    updated_at: datetime
