"""Application settings, loaded from environment / .env file."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Task Tracker API"
    environment: Literal["local", "dev", "prod"] = "local"
    log_level: str = "INFO"

    # Storage backend selector.
    db_backend: Literal["memory", "cosmos"] = "memory"

    # Azure Cosmos DB (only required when db_backend == "cosmos").
    cosmos_endpoint: str | None = None
    cosmos_key: str | None = None
    cosmos_database: str = "tasktracker"

    # JWT auth.
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so settings are parsed once per process."""
    return Settings()
