"""Project members API router (nested under a project)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_member_service
from app.core.security import get_current_user
from app.models.schemas.common import Page
from app.models.schemas.member import Member, MemberCreate, MemberUpdate
from app.services.member_service import MemberNotFoundError, MemberService
from app.services.project_service import ProjectNotFoundError

router = APIRouter(prefix="/projects/{project_id}/members", tags=["members"])


def _project_404(exc: ProjectNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


def _member_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")


@router.post("", response_model=Member, status_code=status.HTTP_201_CREATED)
async def create_member(
    project_id: str,
    payload: MemberCreate,
    user: str = Depends(get_current_user),
    service: MemberService = Depends(get_member_service),
) -> Member:
    try:
        return await service.create(owner=user, project_id=project_id, payload=payload)
    except ProjectNotFoundError as exc:
        raise _project_404(exc)


@router.get("", response_model=Page[Member])
async def list_members(
    project_id: str,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
    service: MemberService = Depends(get_member_service),
) -> Page[Member]:
    try:
        items = await service.list(owner=user, project_id=project_id, limit=limit, offset=offset)
    except ProjectNotFoundError as exc:
        raise _project_404(exc)
    return Page[Member](items=items, limit=limit, offset=offset, count=len(items))


@router.patch("/{member_id}", response_model=Member)
async def update_member(
    project_id: str,
    member_id: str,
    payload: MemberUpdate,
    user: str = Depends(get_current_user),
    service: MemberService = Depends(get_member_service),
) -> Member:
    try:
        return await service.update(
            owner=user, project_id=project_id, member_id=member_id, payload=payload
        )
    except ProjectNotFoundError as exc:
        raise _project_404(exc)
    except MemberNotFoundError:
        raise _member_404()


@router.delete(
    "/{member_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_member(
    project_id: str,
    member_id: str,
    user: str = Depends(get_current_user),
    service: MemberService = Depends(get_member_service),
) -> Response:
    try:
        await service.delete(owner=user, project_id=project_id, member_id=member_id)
    except ProjectNotFoundError as exc:
        raise _project_404(exc)
    except MemberNotFoundError:
        raise _member_404()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
