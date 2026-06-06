"""Health and auth helper endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings

router = APIRouter(tags=["meta"])


class Health(BaseModel):
    status: str
    app: str
    environment: str
    db_backend: str
    image_backend: str


@router.get("/health", response_model=Health)
async def health(settings: Settings = Depends(get_settings)) -> Health:
    # "blob" once an Azure Storage connection string is configured (images
    # persist); "disk" otherwise (ephemeral on Render's free plan).
    image_backend = "blob" if settings.azure_storage_connection_string else "disk"
    return Health(
        status="ok",
        app=settings.app_name,
        environment=settings.environment,
        db_backend=settings.db_backend,
        image_backend=image_backend,
    )


class AuthConfig(BaseModel):
    client_id: str | None
    authority: str


@router.get("/auth/config", response_model=AuthConfig, tags=["auth"])
async def auth_config(settings: Settings = Depends(get_settings)) -> AuthConfig:
    """Public MSAL configuration for the SPA, sourced from the API's environment
    so the Azure client id lives in one place."""
    return AuthConfig(client_id=settings.azure_client_id, authority=settings.azure_authority)
