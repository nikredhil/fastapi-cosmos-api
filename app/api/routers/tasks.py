"""Tasks API router (nested under a project)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_task_service
from app.core.security import get_current_user
from app.models.domain.enums import TaskStatus
from app.models.schemas.common import Page
from app.models.schemas.task import Task, TaskCreate, TaskUpdate
from app.services.task_service import ProjectNotFoundError, TaskNotFoundError, TaskService

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


def _project_404(exc: ProjectNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: str,
    payload: TaskCreate,
    user: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> Task:
    try:
        return await service.create(owner=user, project_id=project_id, payload=payload)
    except ProjectNotFoundError as exc:
        raise _project_404(exc) from exc


@router.get("", response_model=Page[Task])
async def list_tasks(
    project_id: str,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> Page[Task]:
    try:
        items = await service.list(
            owner=user,
            project_id=project_id,
            status=status_filter.value if status_filter else None,
            limit=limit,
            offset=offset,
        )
    except ProjectNotFoundError as exc:
        raise _project_404(exc) from exc
    return Page[Task](items=items, limit=limit, offset=offset, count=len(items))


@router.get("/{task_id}", response_model=Task)
async def get_task(
    project_id: str,
    task_id: str,
    user: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> Task:
    try:
        return await service.get(owner=user, project_id=project_id, task_id=task_id)
    except ProjectNotFoundError as exc:
        raise _project_404(exc) from exc
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        ) from exc


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    project_id: str,
    task_id: str,
    payload: TaskUpdate,
    user: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> Task:
    try:
        return await service.update(
            owner=user, project_id=project_id, task_id=task_id, payload=payload
        )
    except ProjectNotFoundError as exc:
        raise _project_404(exc) from exc
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        ) from exc


@router.delete(
    "/{task_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_task(
    project_id: str,
    task_id: str,
    user: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> Response:
    try:
        await service.delete(owner=user, project_id=project_id, task_id=task_id)
    except ProjectNotFoundError as exc:
        raise _project_404(exc) from exc
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
