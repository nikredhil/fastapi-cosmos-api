"""Buildings API router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_building_service
from app.core.security import get_current_user
from app.models.schemas.building import Building, BuildingCreate, BuildingUpdate
from app.models.schemas.common import Page
from app.services.building_service import BuildingNotFoundError, BuildingService

router = APIRouter(prefix="/buildings", tags=["buildings"])


def _404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")


@router.post("", response_model=Building, status_code=status.HTTP_201_CREATED)
async def create_building(
    payload: BuildingCreate,
    user: str = Depends(get_current_user),
    service: BuildingService = Depends(get_building_service),
) -> Building:
    return await service.create(owner=user, payload=payload)


@router.get("", response_model=Page[Building])
async def list_buildings(
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
    service: BuildingService = Depends(get_building_service),
) -> Page[Building]:
    items = await service.list(owner=user, limit=limit, offset=offset)
    return Page[Building](items=items, limit=limit, offset=offset, count=len(items))


@router.get("/{building_id}", response_model=Building)
async def get_building(
    building_id: str,
    user: str = Depends(get_current_user),
    service: BuildingService = Depends(get_building_service),
) -> Building:
    try:
        return await service.get(owner=user, building_id=building_id)
    except BuildingNotFoundError:
        raise _404()


@router.patch("/{building_id}", response_model=Building)
async def update_building(
    building_id: str,
    payload: BuildingUpdate,
    user: str = Depends(get_current_user),
    service: BuildingService = Depends(get_building_service),
) -> Building:
    try:
        return await service.update(owner=user, building_id=building_id, payload=payload)
    except BuildingNotFoundError:
        raise _404()


@router.delete("/{building_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_building(
    building_id: str,
    user: str = Depends(get_current_user),
    service: BuildingService = Depends(get_building_service),
) -> Response:
    try:
        await service.delete(owner=user, building_id=building_id)
    except BuildingNotFoundError:
        raise _404()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
