"""Local account auth: register and login (email + password)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.core.dependencies import get_user_service
from app.core.security import create_access_token
from app.models.schemas.user import AuthToken, LoginRequest, RegisterRequest
from app.services.user_service import (
    EmailTakenError,
    InvalidCredentialsError,
    UserService,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthToken, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    settings: Settings = Depends(get_settings),
    service: UserService = Depends(get_user_service),
) -> AuthToken:
    try:
        user = await service.register(payload)
    except EmailTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists"
        )
    token = create_access_token(subject=user.email, settings=settings)
    return AuthToken(access_token=token, display_name=user.display_name)


@router.post("/login", response_model=AuthToken)
async def login(
    payload: LoginRequest,
    settings: Settings = Depends(get_settings),
    service: UserService = Depends(get_user_service),
) -> AuthToken:
    try:
        user = await service.authenticate(payload)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    token = create_access_token(subject=user.email, settings=settings)
    return AuthToken(access_token=token, display_name=user.display_name)
