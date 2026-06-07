"""Local account auth: register and login (email + password)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.core.dependencies import get_user_service
from app.core.rate_limit import enforce_login_limit
from app.core.security import create_access_token, get_current_user
from app.models.schemas.user import AuthToken, LoginRequest, RegisterRequest
from app.services.user_service import (
    EmailTakenError,
    InvalidCredentialsError,
    UserService,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthToken, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    payload: RegisterRequest,
    settings: Settings = Depends(get_settings),
    service: UserService = Depends(get_user_service),
) -> AuthToken:
    enforce_login_limit(request, payload.email)
    try:
        user = await service.register(payload)
    except EmailTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists"
        )
    token = create_access_token(subject=user.email, settings=settings)
    return AuthToken(access_token=token, display_name=user.display_name)


@router.get("/me")
async def me(user: str = Depends(get_current_user)) -> dict:
    """Return the stable user id the API derives from your bearer token.

    Local accounts look like ``local:<email>``; Microsoft accounts are the
    Entra object id (a GUID). Used to discover the id to migrate data to.
    """
    return {"user_id": user, "source": "local" if user.startswith("local:") else "microsoft"}


@router.post("/login", response_model=AuthToken)
async def login(
    request: Request,
    payload: LoginRequest,
    settings: Settings = Depends(get_settings),
    service: UserService = Depends(get_user_service),
) -> AuthToken:
    enforce_login_limit(request, payload.email)
    try:
        user = await service.authenticate(payload)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    token = create_access_token(subject=user.email, settings=settings)
    return AuthToken(access_token=token, display_name=user.display_name)
