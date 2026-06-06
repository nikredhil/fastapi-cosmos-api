"""Pluggable storage for uploaded images (contract photos, Aadhaar cards).

Two backends with the same async interface:
- DiskImageStore  — writes to a local directory (dev / no-Azure; ephemeral on
  Render's free plan).
- BlobImageStore  — Azure Blob Storage, so images persist like the Cosmos data.

The backend is chosen at startup: Blob when a connection string is configured,
otherwise disk. See ``build_image_store``.
"""
from __future__ import annotations

import glob
import os

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Media type <-> file extension (the contracts router only accepts these).
EXT_FOR = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
MEDIA_FOR = {ext: media for media, ext in EXT_FOR.items()}


class DiskImageStore:
    """Stores images as files under ``uploads_dir`` (keyed by id + extension)."""

    def __init__(self, uploads_dir: str) -> None:
        self._dir = uploads_dir

    async def save(self, image_id: str, data: bytes, media_type: str) -> None:
        os.makedirs(self._dir, exist_ok=True)
        ext = EXT_FOR.get(media_type, ".bin")
        with open(os.path.join(self._dir, f"{image_id}{ext}"), "wb") as fh:
            fh.write(data)

    async def load(self, image_id: str) -> tuple[bytes, str] | None:
        matches = glob.glob(os.path.join(self._dir, f"{image_id}.*"))
        if not matches:
            return None
        path = matches[0]
        with open(path, "rb") as fh:
            data = fh.read()
        media = MEDIA_FOR.get(os.path.splitext(path)[1], "application/octet-stream")
        return data, media

    async def close(self) -> None:  # symmetry with BlobImageStore
        return None


class BlobImageStore:
    """Stores images as blobs in one Azure Blob Storage container."""

    def __init__(self, connection_string: str, container: str) -> None:
        from azure.storage.blob.aio import BlobServiceClient

        self._service = BlobServiceClient.from_connection_string(connection_string)
        self._container_name = container
        self._ready = False

    async def _container(self):
        client = self._service.get_container_client(self._container_name)
        if not self._ready:
            try:
                await client.create_container()
            except Exception:  # noqa: BLE001 - already exists / race, fine
                pass
            self._ready = True
        return client

    async def save(self, image_id: str, data: bytes, media_type: str) -> None:
        from azure.storage.blob import ContentSettings

        container = await self._container()
        await container.upload_blob(
            name=image_id,
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type=media_type),
        )

    async def load(self, image_id: str) -> tuple[bytes, str] | None:
        from azure.core.exceptions import ResourceNotFoundError

        container = await self._container()
        try:
            stream = await container.download_blob(image_id)
            data = await stream.readall()
            media = stream.properties.content_settings.content_type or "application/octet-stream"
            return data, media
        except ResourceNotFoundError:
            return None

    async def close(self) -> None:
        await self._service.close()


def build_image_store(settings: Settings):
    """Pick the image backend based on settings (Blob if configured, else disk)."""
    if settings.azure_storage_connection_string:
        logger.info("image_store", backend="blob", container=settings.blob_container)
        return BlobImageStore(settings.azure_storage_connection_string, settings.blob_container)
    logger.info("image_store", backend="disk", dir=settings.uploads_dir)
    return DiskImageStore(settings.uploads_dir)


__all__ = ["DiskImageStore", "BlobImageStore", "build_image_store"]
