"""Health and auth helper endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.security import create_access_token

router = APIRouter(tags=["meta"])


class Health(BaseModel):
    status: str
    app: str
    environment: str
    db_backend: str


@router.get("/health", response_model=Health)
async def health(settings: Settings = Depends(get_settings)) -> Health:
    return Health(
        status="ok",
        app=settings.app_name,
        environment=settings.environment,
        db_backend=settings.db_backend,
    )


class TokenRequest(BaseModel):
    username: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/auth/token", response_model=TokenResponse, tags=["auth"])
async def issue_token(
    body: TokenRequest, settings: Settings = Depends(get_settings)
) -> TokenResponse:
    """Dev convenience endpoint: mint a token for any username so the API is
    easy to try in Swagger. Replace with a real IdP flow in production."""
    token = create_access_token(subject=body.username, settings=settings)
    return TokenResponse(access_token=token)
