"""Sprints API router (nested under a project)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_sprint_service
from app.core.security import get_current_user
from app.models.schemas.common import Page
from app.models.schemas.sprint import Sprint, SprintCreate, SprintUpdate
from app.services.project_service import ProjectNotFoundError
from app.services.sprint_service import SprintNotFoundError, SprintService

router = APIRouter(prefix="/projects/{project_id}/sprints", tags=["sprints"])


def _project_404(exc: ProjectNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


def _sprint_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")


@router.post("", response_model=Sprint, status_code=status.HTTP_201_CREATED)
async def create_sprint(
    project_id: str,
    payload: SprintCreate,
    user: str = Depends(get_current_user),
    service: SprintService = Depends(get_sprint_service),
) -> Sprint:
    try:
        return await service.create(owner=user, project_id=project_id, payload=payload)
    except ProjectNotFoundError as exc:
        raise _project_404(exc)


@router.get("", response_model=Page[Sprint])
async def list_sprints(
    project_id: str,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
    service: SprintService = Depends(get_sprint_service),
) -> Page[Sprint]:
    try:
        items = await service.list(owner=user, project_id=project_id, limit=limit, offset=offset)
    except ProjectNotFoundError as exc:
        raise _project_404(exc)
    return Page[Sprint](items=items, limit=limit, offset=offset, count=len(items))


@router.patch("/{sprint_id}", response_model=Sprint)
async def update_sprint(
    project_id: str,
    sprint_id: str,
    payload: SprintUpdate,
    user: str = Depends(get_current_user),
    service: SprintService = Depends(get_sprint_service),
) -> Sprint:
    try:
        return await service.update(
            owner=user, project_id=project_id, sprint_id=sprint_id, payload=payload
        )
    except ProjectNotFoundError as exc:
        raise _project_404(exc)
    except SprintNotFoundError:
        raise _sprint_404()


@router.delete(
    "/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_sprint(
    project_id: str,
    sprint_id: str,
    user: str = Depends(get_current_user),
    service: SprintService = Depends(get_sprint_service),
) -> Response:
    try:
        await service.delete(owner=user, project_id=project_id, sprint_id=sprint_id)
    except ProjectNotFoundError as exc:
        raise _project_404(exc)
    except SprintNotFoundError:
        raise _sprint_404()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
