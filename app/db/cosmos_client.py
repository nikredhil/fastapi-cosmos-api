"""Azure Cosmos DB async client wrapper and Cosmos-backed repository."""
from __future__ import annotations

from typing import Any

from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.core.config import Settings
from app.core.logging import get_logger
from app.db.repositories.base import BaseRepository

logger = get_logger(__name__)


class CosmosConnection:
    """Owns the async CosmosClient and exposes containers.

    Created once at startup and closed at shutdown (see app lifespan).
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.cosmos_endpoint or not settings.cosmos_key:
            raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY are required for the cosmos backend")
        self._client = CosmosClient(settings.cosmos_endpoint, credential=settings.cosmos_key)
        self._database_name = settings.cosmos_database
        self._database: DatabaseProxy | None = None

    async def connect(self) -> None:
        self._database = await self._client.create_database_if_not_exists(self._database_name)
        logger.info("cosmos_connected", database=self._database_name)

    async def get_container(self, name: str, partition_key_field: str) -> ContainerProxy:
        assert self._database is not None, "connect() must be called first"
        from azure.cosmos import PartitionKey

        return await self._database.create_container_if_not_exists(
            id=name, partition_key=PartitionKey(path=f"/{partition_key_field}")
        )

    async def close(self) -> None:
        await self._client.close()
        logger.info("cosmos_closed")


class CosmosRepository(BaseRepository):
    """Repository backed by a single Cosmos container."""

    def __init__(self, container: ContainerProxy, partition_key_field: str) -> None:
        self._container = container
        self._partition_key_field = partition_key_field

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._container.create_item(body=document)

    async def get(self, item_id: str, partition_key: str) -> dict[str, Any] | None:
        try:
            return await self._container.read_item(item=item_id, partition_key=partition_key)
        except CosmosResourceNotFoundError:
            return None

    async def query(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        clauses, params = [], []
        for i, (field, value) in enumerate(filters.items()):
            clauses.append(f"c.{field} = @p{i}")
            params.append({"name": f"@p{i}", "value": value})

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            f"SELECT * FROM c {where} ORDER BY c.created_at DESC "
            f"OFFSET {int(offset)} LIMIT {int(limit)}"
        )
        items = [item async for item in self._container.query_items(query=sql, parameters=params)]
        return items

    async def update(self, document: dict[str, Any]) -> dict[str, Any]:
        return await self._container.upsert_item(body=document)

    async def delete(self, item_id: str, partition_key: str) -> bool:
        try:
            await self._container.delete_item(item=item_id, partition_key=partition_key)
            return True
        except CosmosResourceNotFoundError:
            return False
