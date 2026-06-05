"""Local account (email + password) request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# Lightweight email check — avoids pulling in the email-validator dependency.
_EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=120)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        import re

        v = v.strip().lower()
        if not re.match(_EMAIL_RE, v):
            raise ValueError("invalid email address")
        return v


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    display_name: str


class User(BaseModel):
    """Internal user record (never serialized to clients with the hash)."""

    id: str
    email: str
    password_hash: str
    display_name: str
    created_at: datetime
