"""Back up (and restore) all WiseRent data to a single JSON file.

Cosmos DB's Free Tier keeps only periodic, support-ticket-restorable backups, so
this gives you a self-serve snapshot you control. It dumps every container —
buildings, units, tenants, leases, bills, users — into one timestamped file.

    # Snapshot the live Cosmos data (reads only):
    DB_BACKEND=cosmos COSMOS_ENDPOINT=... COSMOS_KEY=... COSMOS_DATABASE=rentwise \\
        python -m scripts.export_data

    # Restore a snapshot into a backend (creates missing docs; never overwrites):
    DB_BACKEND=cosmos COSMOS_ENDPOINT=... COSMOS_KEY=... COSMOS_DATABASE=rentwise \\
        python -m scripts.export_data --restore scripts/backups/wiserent-20260607T120000Z.json

Restore is safe to re-run: a document whose id already exists under its
partition key is skipped, so it only fills gaps (e.g. into a fresh database).
Run it regularly (cron / a Render scheduled job) to keep offline copies.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone

from app.core.config import Settings, get_settings
from app.db.repositories import (
    bill_repository,
    building_repository,
    lease_repository,
    tenant_repository,
    unit_repository,
    user_repository,
)
from app.db.repositories.base import BaseRepository

# (container name, partition-key field) for every document type we persist.
_CONTAINERS = (
    (building_repository.CONTAINER_NAME, building_repository.PARTITION_KEY_FIELD),
    (unit_repository.CONTAINER_NAME, unit_repository.PARTITION_KEY_FIELD),
    (tenant_repository.CONTAINER_NAME, tenant_repository.PARTITION_KEY_FIELD),
    (lease_repository.CONTAINER_NAME, lease_repository.PARTITION_KEY_FIELD),
    (bill_repository.CONTAINER_NAME, bill_repository.PARTITION_KEY_FIELD),
    (user_repository.CONTAINER_NAME, user_repository.PARTITION_KEY_FIELD),
)

_PAGE = 200


async def _build_backends(settings: Settings):
    """One repository per container, plus an optional connection to close."""
    if settings.db_backend == "cosmos":
        from app.db.cosmos_client import CosmosConnection, CosmosRepository

        connection = CosmosConnection(settings)
        await connection.connect()
        backends: dict[str, BaseRepository] = {}
        for name, pk in _CONTAINERS:
            container = await connection.get_container(name, pk)
            backends[name] = CosmosRepository(container, pk)
        return backends, connection

    if settings.db_backend == "file":
        from app.db.repositories.file_store import JsonFileRepository

        os.makedirs(settings.data_dir, exist_ok=True)
        backends = {
            name: JsonFileRepository(pk, os.path.join(settings.data_dir, f"{name}.json"))
            for name, pk in _CONTAINERS
        }
        return backends, None

    from app.db.repositories.memory import InMemoryRepository

    return {name: InMemoryRepository(pk) for name, pk in _CONTAINERS}, None


async def _all_docs(repo: BaseRepository) -> list[dict]:
    """Page through every document in a container (no owner filter)."""
    out: list[dict] = []
    offset = 0
    while True:
        page = await repo.query(filters=None, limit=_PAGE, offset=offset)
        out.extend(page)
        if len(page) < _PAGE:
            break
        offset += _PAGE
    return out


def _strip_system_fields(doc: dict) -> dict:
    """Drop Cosmos-managed fields (_rid/_etag/…) before re-creating a document."""
    return {k: v for k, v in doc.items() if not k.startswith("_")}


async def export(settings: Settings) -> int:
    backends, connection = await _build_backends(settings)
    try:
        snapshot = {name: await _all_docs(backends[name]) for name, _ in _CONTAINERS}
        total = sum(len(v) for v in snapshot.values())
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        payload = {
            "_meta": {
                "exported_at": stamp,
                "db_backend": settings.db_backend,
                "database": settings.cosmos_database,
                "counts": {name: len(docs) for name, docs in snapshot.items()},
            },
            "containers": snapshot,
        }
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        path = os.path.join(backup_dir, f"wiserent-{stamp}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)

        print(f"Backend: {settings.db_backend}")
        for name, docs in snapshot.items():
            print(f"  {name:<10} {len(docs)}")
        print(f"\nWrote {total} document(s) to {path}")
        return 0
    finally:
        if connection is not None:
            await connection.close()


async def restore(settings: Settings, path: str) -> int:
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    containers = payload.get("containers", {})

    backends, connection = await _build_backends(settings)
    try:
        pk_by_name = dict(_CONTAINERS)
        created = skipped = 0
        for name, _ in _CONTAINERS:
            repo = backends[name]
            pk_field = pk_by_name[name]
            for doc in containers.get(name, []):
                doc = _strip_system_fields(doc)
                item_id, pk = doc.get("id"), doc.get(pk_field)
                if item_id is None or pk is None:
                    print(f"  skip {name} doc — missing id/{pk_field}")
                    skipped += 1
                    continue
                if await repo.get(item_id, pk) is not None:
                    skipped += 1
                    continue
                await repo.create(doc)
                created += 1
            print(f"  {name:<10} restored")
        print(f"\nDone. Created {created}, skipped {skipped} (already present or invalid).")
        return 0
    finally:
        if connection is not None:
            await connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Back up or restore all WiseRent data.")
    parser.add_argument(
        "--restore", metavar="FILE",
        help="Restore from a backup JSON file instead of exporting.",
    )
    args = parser.parse_args()
    settings = get_settings()
    if args.restore:
        raise SystemExit(asyncio.run(restore(settings, args.restore)))
    raise SystemExit(asyncio.run(export(settings)))


if __name__ == "__main__":
    main()
