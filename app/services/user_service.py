"""Business logic for local email/password accounts."""
from __future__ import annotations

from datetime import datetime, timezone

import bcrypt

from app.db.repositories.user_repository import UserRepository
from app.models.schemas.user import LoginRequest, RegisterRequest, User


def _hash_password(password: str) -> str:
    # bcrypt operates on the first 72 bytes; truncate explicitly so longer
    # passwords don't raise on newer bcrypt builds.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))
    except ValueError:
        return False


class EmailTakenError(Exception):
    """Raised when registering an email that already has an account."""


class InvalidCredentialsError(Exception):
    """Raised when login email/password don't match a stored account."""


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repo = repository

    async def register(self, payload: RegisterRequest) -> User:
        if await self._repo.get_by_email(payload.email) is not None:
            raise EmailTakenError(payload.email)
        document = {
            "id": payload.email,
            "email": payload.email,
            "password_hash": _hash_password(payload.password),
            "display_name": payload.display_name or payload.email.split("@")[0],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        created = await self._repo.create(document)
        return User(**created)

    async def authenticate(self, payload: LoginRequest) -> User:
        doc = await self._repo.get_by_email(payload.email)
        if doc is None or not _verify_password(payload.password, doc["password_hash"]):
            raise InvalidCredentialsError(payload.email)
        return User(**doc)


__all__ = ["UserService", "EmailTakenError", "InvalidCredentialsError"]
