"""Task request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain.enums import ItemType, Priority, TaskStatus


class Comment(BaseModel):
    id: str
    author: str
    body: str
    created_at: datetime


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    item_type: ItemType = ItemType.TASK
    points: int | None = Field(default=None, ge=0, le=100)
    sprint_id: str | None = Field(default=None, description="Target sprint; null = backlog")
    assignee_id: str | None = Field(default=None, description="Assigned member id")
    due_date: str | None = None
    tags: list[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    status: TaskStatus | None = None
    priority: Priority | None = None
    item_type: ItemType | None = None
    points: int | None = Field(default=None, ge=0, le=100)
    sprint_id: str | None = None
    assignee_id: str | None = None
    due_date: str | None = None
    tags: list[str] | None = None


class Task(BaseModel):
    id: str
    project_id: str = Field(description="Parent project (partition key)")
    number: int | None = Field(default=None, description="Per-project item number")
    key: str | None = Field(default=None, description="Display key, e.g. WEB-12")
    title: str
    description: str | None = None
    status: TaskStatus
    priority: Priority
    item_type: ItemType = ItemType.TASK
    points: int | None = None
    sprint_id: str | None = None
    assignee_id: str | None = None
    assignee_name: str | None = Field(default=None, description="Denormalized for display")
    due_date: str | None = None
    tags: list[str] = Field(default_factory=list)
    comments: list[Comment] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
