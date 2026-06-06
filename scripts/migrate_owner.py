"""Re-point a user's buildings from one owner id to another (account migration).

Only **buildings** carry an ``owner`` (the per-user partition key). Units,
tenants, leases, and bills hang off ``building_id``, so moving the buildings
moves all of a landlord's data with them — no other container is touched.

Typical use: a landlord created data under a local account
(``local:<email>``) and now wants to sign in with Microsoft (an Entra object
id). After their first Microsoft login, GET /auth/me shows the new id; run:

    # Dry run first (default) — lists what WOULD change and writes a backup:
    DB_BACKEND=cosmos COSMOS_ENDPOINT=... COSMOS_KEY=... COSMOS_DATABASE=rentwise \\
        python -m scripts.migrate_owner --from "local:you@example.com" --to "<entra-oid>"

    # Then apply for real:
    ... python -m scripts.migrate_owner --from "local:you@example.com" --to "<entra-oid>" --apply

It is safe to re-run: a building already present under the destination owner is
skipped. Nothing is deleted until its copy exists under the new owner.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone

from app.core.config import get_settings
from app.db.repositories import building_repository
from app.db.repositories.building_repository import BuildingRepository


async def _build_buildings_backend(settings):
    """Construct just the 'buildings' backend for the configured store."""
    name = building_repository.CONTAINER_NAME  # "buildings"
    pk = building_repository.PARTITION_KEY_FIELD  # "owner"

    if settings.db_backend == "cosmos":
        from app.db.cosmos_client import CosmosConnection, CosmosRepository

        connection = CosmosConnection(settings)
        await connection.connect()
        container = await connection.get_container(name, pk)
        return CosmosRepository(container, pk), connection

    if settings.db_backend == "file":
        from app.db.repositories.file_store import JsonFileRepository

        os.makedirs(settings.data_dir, exist_ok=True)
        return JsonFileRepository(pk, os.path.join(settings.data_dir, f"{name}.json")), None

    from app.db.repositories.memory import InMemoryRepository

    return InMemoryRepository(pk), None


async def _all_for_owner(repo: BuildingRepository, owner: str) -> list[dict]:
    """Page through every building owned by ``owner``."""
    out: list[dict] = []
    offset = 0
    while True:
        page = await repo.list_for_owner(owner, limit=200, offset=offset)
        if not page:
            break
        out.extend(page)
        if len(page) < 200:
            break
        offset += 200
    return out


def _strip_system_fields(doc: dict) -> dict:
    """Drop Cosmos-managed fields (_rid/_etag/…) before re-creating a document."""
    return {k: v for k, v in doc.items() if not k.startswith("_")}


async def run(from_owner: str, to_owner: str, apply: bool) -> int:
    if from_owner == to_owner:
        print("--from and --to are identical; nothing to do.")
        return 0

    settings = get_settings()
    backend, connection = await _build_buildings_backend(settings)
    repo = BuildingRepository(backend)
    try:
        buildings = await _all_for_owner(repo, from_owner)
        print(f"Backend: {settings.db_backend}")
        print(f"Found {len(buildings)} building(s) owned by {from_owner!r}.")
        for b in buildings:
            print(f"  - {b.get('id')}  {b.get('name')!r}")

        if not buildings:
            print("Nothing to migrate.")
            return 0

        # Always write a backup of the source documents before any change.
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, f"buildings-{stamp}.json")
        with open(backup_path, "w", encoding="utf-8") as fh:
            json.dump(buildings, fh, indent=2, default=str)
        print(f"Backup written: {backup_path}")

        if not apply:
            print("\nDRY RUN — no changes made. Re-run with --apply to migrate.")
            return 0

        existing_dest = {b.get("id") for b in await _all_for_owner(repo, to_owner)}
        moved = skipped = 0
        for b in buildings:
            bid = b.get("id")
            if bid in existing_dest:
                print(f"  skip {bid} — already exists under destination owner.")
                skipped += 1
                continue
            new_doc = _strip_system_fields(b)
            new_doc["owner"] = to_owner
            await repo.create(new_doc)  # create copy under new owner first…
            await repo.delete(bid, from_owner)  # …then remove the old copy
            print(f"  moved {bid}  {b.get('name')!r}")
            moved += 1

        print(f"\nDone. Moved {moved}, skipped {skipped}.")
        print(f"If anything looks wrong, the source docs are in {backup_path}.")
        return 0
    finally:
        if connection is not None:
            await connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate a landlord's buildings to a new owner id.")
    parser.add_argument("--from", dest="from_owner", required=True,
                        help="Current owner id, e.g. 'local:you@example.com'")
    parser.add_argument("--to", dest="to_owner", required=True,
                        help="New owner id (Microsoft Entra object id from GET /auth/me)")
    parser.add_argument("--apply", action="store_true",
                        help="Actually perform the migration (default is a dry run).")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.from_owner, args.to_owner, args.apply)))


if __name__ == "__main__":
    main()
