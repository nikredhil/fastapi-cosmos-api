"""In-memory repository — zero-setup backend for local dev, demos, and tests."""
from __future__ import annotations

import asyncio
from typing import Any

from app.db.repositories.base import BaseRepository


class InMemoryRepository(BaseRepository):
    """Dict-backed store. Not durable; data lives for the process lifetime."""

    def __init__(self, partition_key_field: str) -> None:
        self._partition_key_field = partition_key_field
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            self._store[document["id"]] = dict(document)
            return dict(document)

    async def get(self, item_id: str, partition_key: str) -> dict[str, Any] | None:
        doc = self._store.get(item_id)
        if doc is None or doc.get(self._partition_key_field) != partition_key:
            return None
        return dict(doc)

    async def query(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        matches = [
            dict(doc)
            for doc in self._store.values()
            if all(doc.get(k) == v for k, v in filters.items())
        ]
        matches.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        return matches[offset : offset + limit]

    async def update(self, document: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            self._store[document["id"]] = dict(document)
            return dict(document)

    async def delete(self, item_id: str, partition_key: str) -> bool:
        async with self._lock:
            doc = self._store.get(item_id)
            if doc is None or doc.get(self._partition_key_field) != partition_key:
                return False
            del self._store[item_id]
            return True
