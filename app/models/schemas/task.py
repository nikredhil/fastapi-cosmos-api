"""Task request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain.enums import Priority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    assignee: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    status: TaskStatus | None = None
    priority: Priority | None = None
    assignee: str | None = None


class Task(BaseModel):
    id: str
    project_id: str = Field(description="Parent project (partition key)")
    title: str
    description: str | None = None
    status: TaskStatus
    priority: Priority
    assignee: str | None = None
    created_at: datetime
    updated_at: datetime
