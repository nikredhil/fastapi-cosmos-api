"""Dashboard API router — aggregated KPIs for the signed-in landlord."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_dashboard_service
from app.core.security import get_current_user
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    period: str | None = Query(default=None, description="Month YYYY-MM; defaults to current"),
    user: str = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    return await service.summary(owner=user, period=period)
