"""Projects API router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_project_service
from app.core.security import get_current_user
from app.models.schemas.common import Page
from app.models.schemas.project import Project, ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectNotFoundError, ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    user: str = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> Project:
    return await service.create(owner=user, payload=payload)


@router.get("", response_model=Page[Project])
async def list_projects(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> Page[Project]:
    items = await service.list(owner=user, limit=limit, offset=offset)
    return Page[Project](items=items, limit=limit, offset=offset, count=len(items))


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    user: str = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> Project:
    try:
        return await service.get(owner=user, project_id=project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    user: str = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> Project:
    try:
        return await service.update(owner=user, project_id=project_id, payload=payload)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.delete(
    "/{project_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_project(
    project_id: str,
    user: str = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> Response:
    try:
        await service.delete(owner=user, project_id=project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
