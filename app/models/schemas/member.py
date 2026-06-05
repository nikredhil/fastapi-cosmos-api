"""Project member (employee) request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role: str | None = Field(default=None, max_length=120)
    avatar_color: str | None = Field(
        default=None, description="Hex color for the member's avatar, e.g. #6366f1"
    )


class MemberUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: str | None = Field(default=None, max_length=120)
    avatar_color: str | None = None


class Member(BaseModel):
    id: str
    project_id: str = Field(description="Parent project (partition key)")
    name: str
    role: str | None = None
    avatar_color: str | None = None
    created_at: datetime
