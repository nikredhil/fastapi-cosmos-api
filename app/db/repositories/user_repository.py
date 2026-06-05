"""Data access for local user accounts, delegating to a storage backend."""
from __future__ import annotations

from typing import Any

from app.db.repositories.base import BaseRepository

# Users are keyed by email; id == email so get(email, email) resolves a user.
PARTITION_KEY_FIELD = "email"
CONTAINER_NAME = "users"


class UserRepository:
    def __init__(self, backend: BaseRepository) -> None:
        self._backend = backend

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._backend.create(document)

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        return await self._backend.get(email, email)
