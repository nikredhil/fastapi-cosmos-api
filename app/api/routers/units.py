"""Units API router (nested under a building)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_unit_service
from app.core.security import get_current_user
from app.models.schemas.common import Page
from app.models.schemas.unit import Unit, UnitCreate, UnitUpdate
from app.services.building_service import BuildingNotFoundError
from app.services.unit_service import UnitNotFoundError, UnitService

router = APIRouter(prefix="/buildings/{building_id}/units", tags=["units"])


def _building_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")


def _unit_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")


@router.post("", response_model=Unit, status_code=status.HTTP_201_CREATED)
async def create_unit(
    building_id: str,
    payload: UnitCreate,
    user: str = Depends(get_current_user),
    service: UnitService = Depends(get_unit_service),
) -> Unit:
    try:
        return await service.create(owner=user, building_id=building_id, payload=payload)
    except BuildingNotFoundError:
        raise _building_404()


@router.get("", response_model=Page[Unit])
async def list_units(
    building_id: str,
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
    service: UnitService = Depends(get_unit_service),
) -> Page[Unit]:
    try:
        items = await service.list(owner=user, building_id=building_id, limit=limit, offset=offset)
    except BuildingNotFoundError:
        raise _building_404()
    return Page[Unit](items=items, limit=limit, offset=offset, count=len(items))


@router.patch("/{unit_id}", response_model=Unit)
async def update_unit(
    building_id: str,
    unit_id: str,
    payload: UnitUpdate,
    user: str = Depends(get_current_user),
    service: UnitService = Depends(get_unit_service),
) -> Unit:
    try:
        return await service.update(
            owner=user, building_id=building_id, unit_id=unit_id, payload=payload
        )
    except BuildingNotFoundError:
        raise _building_404()
    except UnitNotFoundError:
        raise _unit_404()


@router.delete(
    "/{unit_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_unit(
    building_id: str,
    unit_id: str,
    user: str = Depends(get_current_user),
    service: UnitService = Depends(get_unit_service),
) -> Response:
    try:
        await service.delete(owner=user, building_id=building_id, unit_id=unit_id)
    except BuildingNotFoundError:
        raise _building_404()
    except UnitNotFoundError:
        raise _unit_404()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
