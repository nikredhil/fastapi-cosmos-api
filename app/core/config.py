"""Application settings, loaded from environment / .env file."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "WiseRent — Rental Manager"
    environment: Literal["local", "dev", "prod"] = "local"
    log_level: str = "INFO"

    # Allowed CORS origins. "*" (default) allows any origin — fine for local dev.
    # In production set a comma-separated allowlist, e.g.
    #   CORS_ORIGINS="https://wiserent.in,https://www.wiserent.in"
    cors_origins: str = "*"

    # Storage backend selector. Defaults to "file" so tenant/rent data survives
    # restarts out of the box; switch to "cosmos" for a hosted deployment.
    db_backend: Literal["memory", "file", "cosmos"] = "file"

    # Directory for the JSON-file backend (only used when db_backend == "file").
    data_dir: str = "./data"

    # Where uploaded contract images are stored on disk (used unless Azure Blob
    # Storage is configured below). Served back via the contracts API.
    uploads_dir: str = "./data/uploads"

    # Azure Blob Storage for uploaded images. When the connection string is set,
    # images persist in Blob Storage instead of the (ephemeral) local disk.
    azure_storage_connection_string: str | None = None
    blob_container: str = "uploads"

    # Anthropic (Claude) — used to parse uploaded contract photos into structured
    # fields. When unset, the contract-parse endpoint degrades to manual entry.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-4-8"

    # Azure Cosmos DB (only required when db_backend == "cosmos").
    cosmos_endpoint: str | None = None
    cosmos_key: str | None = None
    cosmos_database: str = "rentwise"
    # When set, create the Cosmos database with this shared throughput (RU/s) so
    # all containers share one pool. Use 1000 on an account with the Free Tier
    # discount applied to stay $0. Leave unset for Serverless accounts.
    cosmos_shared_throughput: int | None = None

    # Microsoft Entra ID (Azure AD) sign-in. The SPA authenticates with Microsoft
    # via MSAL and sends an ID token; the API validates it against Microsoft's
    # public keys. azure_client_id is the app registration's Application (client) ID.
    azure_client_id: str | None = None
    azure_authority: str = "https://login.microsoftonline.com/common"

    # Local email/password accounts. The API mints its own HS256 token for these,
    # alongside (and distinct from) the RS256 tokens Microsoft issues.
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so settings are parsed once per process."""
    return Settings()
