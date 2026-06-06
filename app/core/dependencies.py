"""FastAPI dependency providers.

Services are constructed once at startup and stored on ``app.state``; these
providers simply hand them to route handlers.
"""
from __future__ import annotations

from fastapi import Request

from app.services.bill_service import BillService
from app.services.building_service import BuildingService
from app.services.dashboard_service import DashboardService
from app.services.lease_service import LeaseService
from app.services.tenant_service import TenantService
from app.services.unit_service import UnitService
from app.services.user_service import UserService


def get_user_service(request: Request) -> UserService:
    return request.app.state.user_service


def get_building_service(request: Request) -> BuildingService:
    return request.app.state.building_service


def get_unit_service(request: Request) -> UnitService:
    return request.app.state.unit_service


def get_tenant_service(request: Request) -> TenantService:
    return request.app.state.tenant_service


def get_lease_service(request: Request) -> LeaseService:
    return request.app.state.lease_service


def get_bill_service(request: Request) -> BillService:
    return request.app.state.bill_service


def get_dashboard_service(request: Request) -> DashboardService:
    return request.app.state.dashboard_service


def get_image_store(request: Request):
    """The configured image backend (Azure Blob or local disk)."""
    return request.app.state.image_store
