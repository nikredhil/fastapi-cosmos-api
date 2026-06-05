"""Round-trip tests for the durable JSON-file repository backend."""
from __future__ import annotations

from app.db.repositories.file_store import JsonFileRepository


async def test_file_store_persists_across_instances(tmp_path) -> None:
    path = str(tmp_path / "tasks.json")

    repo = JsonFileRepository("project_id", path)
    await repo.create(
        {"id": "t1", "project_id": "p1", "title": "Persist me", "created_at": "2026-06-05"}
    )

    # A fresh instance pointed at the same file sees the persisted document.
    reopened = JsonFileRepository("project_id", path)
    doc = await reopened.get("t1", "p1")
    assert doc is not None
    assert doc["title"] == "Persist me"

    # Partition isolation still holds.
    assert await reopened.get("t1", "other") is None

    # Delete is durable too.
    assert await reopened.delete("t1", "p1") is True
    again = JsonFileRepository("project_id", path)
    assert await again.get("t1", "p1") is None


async def test_file_store_corrupt_file_starts_empty(tmp_path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{ not valid json")
    repo = JsonFileRepository("project_id", str(path))
    assert await repo.query() == []
