"""Leases/contracts API router (nested under a building)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_lease_service
from app.core.security import get_current_user
from app.models.schemas.common import Page
from app.models.schemas.lease import Lease, LeaseCreate, LeaseUpdate
from app.services.building_service import BuildingNotFoundError
from app.services.lease_service import LeaseNotFoundError, LeaseService

router = APIRouter(prefix="/buildings/{building_id}/leases", tags=["leases"])


def _building_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")


def _lease_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")


@router.post("", response_model=Lease, status_code=status.HTTP_201_CREATED)
async def create_lease(
    building_id: str,
    payload: LeaseCreate,
    user: str = Depends(get_current_user),
    service: LeaseService = Depends(get_lease_service),
) -> Lease:
    try:
        return await service.create(owner=user, building_id=building_id, payload=payload)
    except BuildingNotFoundError:
        raise _building_404()


@router.get("", response_model=Page[Lease])
async def list_leases(
    building_id: str,
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
    service: LeaseService = Depends(get_lease_service),
) -> Page[Lease]:
    try:
        items = await service.list(owner=user, building_id=building_id, limit=limit, offset=offset)
    except BuildingNotFoundError:
        raise _building_404()
    return Page[Lease](items=items, limit=limit, offset=offset, count=len(items))


@router.patch("/{lease_id}", response_model=Lease)
async def update_lease(
    building_id: str,
    lease_id: str,
    payload: LeaseUpdate,
    user: str = Depends(get_current_user),
    service: LeaseService = Depends(get_lease_service),
) -> Lease:
    try:
        return await service.update(
            owner=user, building_id=building_id, lease_id=lease_id, payload=payload
        )
    except BuildingNotFoundError:
        raise _building_404()
    except LeaseNotFoundError:
        raise _lease_404()


@router.delete(
    "/{lease_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_lease(
    building_id: str,
    lease_id: str,
    user: str = Depends(get_current_user),
    service: LeaseService = Depends(get_lease_service),
) -> Response:
    try:
        await service.delete(owner=user, building_id=building_id, lease_id=lease_id)
    except BuildingNotFoundError:
        raise _building_404()
    except LeaseNotFoundError:
        raise _lease_404()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
