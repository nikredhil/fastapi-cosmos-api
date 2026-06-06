"""Contract upload + parse API (nested under a building).

Upload a photo/scan of a rental agreement or an Aadhaar card; it is stored via
the configured image backend (Azure Blob Storage in prod, local disk otherwise)
and — for /parse, if Claude is configured — parsed into structured lease fields.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from app.core.config import get_settings
from app.core.dependencies import get_building_service, get_image_store
from app.core.security import get_current_user
from app.services.building_service import BuildingNotFoundError, BuildingService
from app.services.contract_parser import is_enabled, parse_contract_images

router = APIRouter(prefix="/buildings/{building_id}/contracts", tags=["contracts"])

_ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


def _building_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")


async def _assert_building(buildings: BuildingService, user: str, building_id: str) -> None:
    try:
        await buildings.get(owner=user, building_id=building_id)
    except BuildingNotFoundError:
        raise _building_404()


async def _read_valid_image(file: UploadFile) -> tuple[bytes, str]:
    media_type = file.content_type or ""
    if media_type not in _ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a JPEG, PNG, WEBP, or GIF image.",
        )
    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image is larger than 10 MB.",
        )
    return data, media_type


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    building_id: str,
    file: UploadFile = File(...),
    user: str = Depends(get_current_user),
    buildings: BuildingService = Depends(get_building_service),
    store=Depends(get_image_store),
) -> dict:
    """Store an image (e.g. Aadhaar card) and return its id — no parsing."""
    await _assert_building(buildings, user, building_id)
    data, media_type = await _read_valid_image(file)
    image_id = uuid.uuid4().hex
    await store.save(image_id, data, media_type)
    return {"image_id": image_id}


@router.post("/parse", status_code=status.HTTP_201_CREATED)
async def upload_and_parse(
    building_id: str,
    files: list[UploadFile] = File(...),
    user: str = Depends(get_current_user),
    buildings: BuildingService = Depends(get_building_service),
    store=Depends(get_image_store),
) -> dict:
    """Store every page of an agreement and parse them together into fields."""
    await _assert_building(buildings, user, building_id)
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")

    image_ids: list[str] = []
    images: list[tuple[bytes, str]] = []
    for file in files:
        data, media_type = await _read_valid_image(file)
        image_id = uuid.uuid4().hex
        await store.save(image_id, data, media_type)
        image_ids.append(image_id)
        images.append((data, media_type))

    settings = get_settings()
    parsed = await run_in_threadpool(parse_contract_images, images, settings)
    return {
        "contract_image_id": image_ids[0],
        "contract_image_ids": image_ids,
        "enabled": is_enabled(settings),
        **parsed,
    }


@router.get("/{image_id}")
async def get_contract_image(
    building_id: str,
    image_id: str,
    user: str = Depends(get_current_user),
    buildings: BuildingService = Depends(get_building_service),
    store=Depends(get_image_store),
) -> Response:
    await _assert_building(buildings, user, building_id)
    # image_id is a uuid hex we generated; guard against traversal/odd keys.
    if not image_id.isalnum():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    found = await store.load(image_id)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    data, media_type = found
    return Response(content=data, media_type=media_type)
