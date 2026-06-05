"""Application settings, loaded from environment / .env file."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Sentinel default — safe for local dev, but must be overridden outside "local".
DEFAULT_JWT_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Task Tracker API"
    environment: Literal["local", "dev", "prod"] = "local"
    log_level: str = "INFO"

    # Comma-separated list of allowed CORS origins. "*" allows any origin
    # (acceptable for local dev; set explicit origins in dev/prod).
    cors_origins: list[str] = ["*"]

    # Storage backend selector.
    db_backend: Literal["memory", "cosmos"] = "memory"

    # Azure Cosmos DB (only required when db_backend == "cosmos").
    cosmos_endpoint: str | None = None
    cosmos_key: str | None = None
    cosmos_database: str = "tasktracker"

    # JWT auth.
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Accept a comma-separated string (e.g. from an env var) as a list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _validate_for_environment(self) -> Settings:
        """Fail fast on unsafe / incomplete configuration outside local dev."""
        if self.environment != "local":
            if self.jwt_secret == DEFAULT_JWT_SECRET:
                raise ValueError(
                    "JWT_SECRET must be overridden when ENVIRONMENT is not 'local'."
                )
            if "*" in self.cors_origins:
                raise ValueError(
                    "CORS_ORIGINS must list explicit origins (not '*') "
                    "when ENVIRONMENT is not 'local'."
                )

        if self.db_backend == "cosmos" and not (self.cosmos_endpoint and self.cosmos_key):
            raise ValueError(
                "COSMOS_ENDPOINT and COSMOS_KEY are required when DB_BACKEND='cosmos'."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so settings are parsed once per process."""
    return Settings()
