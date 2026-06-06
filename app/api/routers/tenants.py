"""Tenants API router (nested under a building)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_bill_service, get_tenant_service
from app.core.security import get_current_user
from app.models.schemas.common import Page
from app.models.schemas.tenant import Tenant, TenantCreate, TenantUpdate
from app.services.bill_service import BillService
from app.services.building_service import BuildingNotFoundError
from app.services.tenant_service import TenantNotFoundError, TenantService

router = APIRouter(prefix="/buildings/{building_id}/tenants", tags=["tenants"])


def _building_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")


def _tenant_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")


@router.post("", response_model=Tenant, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    building_id: str,
    payload: TenantCreate,
    user: str = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> Tenant:
    try:
        return await service.create(owner=user, building_id=building_id, payload=payload)
    except BuildingNotFoundError:
        raise _building_404()


@router.get("", response_model=Page[Tenant])
async def list_tenants(
    building_id: str,
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> Page[Tenant]:
    try:
        items = await service.list(owner=user, building_id=building_id, limit=limit, offset=offset)
    except BuildingNotFoundError:
        raise _building_404()
    return Page[Tenant](items=items, limit=limit, offset=offset, count=len(items))


@router.get("/{tenant_id}", response_model=Tenant)
async def get_tenant(
    building_id: str,
    tenant_id: str,
    user: str = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> Tenant:
    try:
        return await service.get(owner=user, building_id=building_id, tenant_id=tenant_id)
    except BuildingNotFoundError:
        raise _building_404()
    except TenantNotFoundError:
        raise _tenant_404()


@router.patch("/{tenant_id}", response_model=Tenant)
async def update_tenant(
    building_id: str,
    tenant_id: str,
    payload: TenantUpdate,
    user: str = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
    bills: BillService = Depends(get_bill_service),
) -> Tenant:
    try:
        tenant = await service.update(
            owner=user, building_id=building_id, tenant_id=tenant_id, payload=payload
        )
    except BuildingNotFoundError:
        raise _building_404()
    except TenantNotFoundError:
        raise _tenant_404()
    # If the rent changed, re-price the tenant's open (unpaid) rent bills so the
    # Rent & Bills tab reflects it — independent of the frontend.
    if "monthly_rent" in payload.model_dump(exclude_unset=True) and tenant.monthly_rent > 0:
        await bills.sync_tenant_rent(
            owner=user,
            building_id=building_id,
            tenant_id=tenant_id,
            monthly_rent=tenant.monthly_rent,
        )
    return tenant


@router.delete(
    "/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_tenant(
    building_id: str,
    tenant_id: str,
    user: str = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> Response:
    try:
        await service.delete(owner=user, building_id=building_id, tenant_id=tenant_id)
    except BuildingNotFoundError:
        raise _building_404()
    except TenantNotFoundError:
        raise _tenant_404()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
