"""JSON-file repository — durable local backend that survives restarts.

Mirrors :class:`InMemoryRepository` exactly, but loads its document dict from a
JSON file on construction and re-serializes it to disk after every write. Stays
faithful to the codebase's "documents are plain dicts" model, so it works for
the flexible task documents (embedded comments/tags lists) without a schema.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from app.db.repositories.base import BaseRepository


class JsonFileRepository(BaseRepository):
    """Dict-backed store that persists to a single JSON file."""

    def __init__(self, partition_key_field: str, file_path: str) -> None:
        self._partition_key_field = partition_key_field
        self._file_path = file_path
        self._lock = asyncio.Lock()
        self._store: dict[str, dict[str, Any]] = self._load()

    def _load(self) -> dict[str, dict[str, Any]]:
        if not os.path.exists(self._file_path):
            return {}
        try:
            with open(self._file_path, encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable file: start empty rather than crash on boot.
            return {}

    def _flush(self) -> None:
        os.makedirs(os.path.dirname(self._file_path) or ".", exist_ok=True)
        tmp = f"{self._file_path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self._store, fh, indent=2)
        os.replace(tmp, self._file_path)  # atomic on POSIX

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            self._store[document["id"]] = dict(document)
            self._flush()
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
            self._flush()
            return dict(document)

    async def delete(self, item_id: str, partition_key: str) -> bool:
        async with self._lock:
            doc = self._store.get(item_id)
            if doc is None or doc.get(self._partition_key_field) != partition_key:
                return False
            del self._store[item_id]
            self._flush()
            return True
