"""Domain enumerations."""
from __future__ import annotations

from enum import Enum


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ItemType(str, Enum):
    """Work-item type, mirroring Zoho Sprints' Story / Task / Bug."""

    STORY = "story"
    TASK = "task"
    BUG = "bug"


class SprintStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
