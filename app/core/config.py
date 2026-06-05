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
    db_backend: Literal["memory", "file", "cosmos"] = "memory"

    # Directory for the JSON-file backend (only used when db_backend == "file").
    data_dir: str = "./data"

    # Azure Cosmos DB (only required when db_backend == "cosmos").
    cosmos_endpoint: str | None = None
    cosmos_key: str | None = None
    cosmos_database: str = "tasktracker"

    # Microsoft Entra ID (Azure AD) sign-in. The SPA authenticates with Microsoft
    # via MSAL and sends an ID token; the API validates it against Microsoft's
    # public keys. azure_client_id is the app registration's Application (client) ID.
    azure_client_id: str | None = None
    azure_authority: str = "https://login.microsoftonline.com/common"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so settings are parsed once per process."""
    return Settings()
