"""Shared schema types."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Simple paginated response envelope."""

    items: list[T]
    limit: int
    offset: int
    count: int = Field(description="Number of items in this page")
