"""Contract upload + parse API (nested under a building).

Upload a photo/scan of a rental agreement; it is stored on disk and (if Claude
is configured) parsed into structured fields the UI uses to prefill a lease.
"""
from __future__ import annotations

import glob
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.dependencies import get_building_service
from app.core.security import get_current_user
from app.services.building_service import BuildingNotFoundError, BuildingService
from app.services.contract_parser import is_enabled, parse_contract_image

router = APIRouter(prefix="/buildings/{building_id}/contracts", tags=["contracts"])

_ALLOWED = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


def _building_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")


def _save_upload(data: bytes, media_type: str) -> str:
    """Validate + persist an uploaded image; return its generated id."""
    if media_type not in _ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a JPEG, PNG, WEBP, or GIF image.",
        )
    if len(data) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image is larger than 10 MB.",
        )
    settings = get_settings()
    os.makedirs(settings.uploads_dir, exist_ok=True)
    image_id = uuid.uuid4().hex
    path = os.path.join(settings.uploads_dir, f"{image_id}{_ALLOWED[media_type]}")
    with open(path, "wb") as fh:
        fh.write(data)
    return image_id


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    building_id: str,
    file: UploadFile = File(...),
    user: str = Depends(get_current_user),
    buildings: BuildingService = Depends(get_building_service),
) -> dict:
    """Store an image (e.g. Aadhaar card) and return its id — no parsing."""
    try:
        await buildings.get(owner=user, building_id=building_id)
    except BuildingNotFoundError:
        raise _building_404()
    data = await file.read()
    image_id = _save_upload(data, file.content_type or "")
    return {"image_id": image_id}


@router.post("/parse", status_code=status.HTTP_201_CREATED)
async def upload_and_parse(
    building_id: str,
    file: UploadFile = File(...),
    user: str = Depends(get_current_user),
    buildings: BuildingService = Depends(get_building_service),
) -> dict:
    # Ownership check — only the building's landlord may upload to it.
    try:
        await buildings.get(owner=user, building_id=building_id)
    except BuildingNotFoundError:
        raise _building_404()

    media_type = file.content_type or ""
    if media_type not in _ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a JPEG, PNG, WEBP, or GIF image of the contract.",
        )
    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image is larger than 10 MB.",
        )

    settings = get_settings()
    os.makedirs(settings.uploads_dir, exist_ok=True)
    image_id = uuid.uuid4().hex
    path = os.path.join(settings.uploads_dir, f"{image_id}{_ALLOWED[media_type]}")
    with open(path, "wb") as fh:
        fh.write(data)

    parsed = await run_in_threadpool(parse_contract_image, data, media_type, settings)
    return {"contract_image_id": image_id, "enabled": is_enabled(settings), **parsed}


@router.get("/{image_id}")
async def get_contract_image(
    building_id: str,
    image_id: str,
    user: str = Depends(get_current_user),
    buildings: BuildingService = Depends(get_building_service),
) -> FileResponse:
    try:
        await buildings.get(owner=user, building_id=building_id)
    except BuildingNotFoundError:
        raise _building_404()

    settings = get_settings()
    # image_id is a uuid hex we generated; guard against path traversal anyway.
    if not image_id.isalnum():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    matches = glob.glob(os.path.join(settings.uploads_dir, f"{image_id}.*"))
    if not matches:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return FileResponse(matches[0])
