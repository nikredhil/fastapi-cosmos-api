"""Project request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class Project(BaseModel):
    id: str
    owner: str = Field(description="Subject of the user who owns the project (partition key)")
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
