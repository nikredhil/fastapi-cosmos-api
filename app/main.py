"""Application entry point: lifespan wiring, middleware, router registration."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    auth,
    bills,
    buildings,
    chat,
    contracts,
    dashboard,
    health,
    leases,
    tenants,
    units,
)
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.repositories import (
    bill_repository,
    building_repository,
    lease_repository,
    tenant_repository,
    unit_repository,
    user_repository,
)
from app.db.repositories.base import BaseRepository
from app.db.repositories.bill_repository import BillRepository
from app.db.repositories.building_repository import BuildingRepository
from app.db.repositories.file_store import JsonFileRepository
from app.db.repositories.lease_repository import LeaseRepository
from app.db.repositories.memory import InMemoryRepository
from app.db.repositories.tenant_repository import TenantRepository
from app.db.repositories.unit_repository import UnitRepository
from app.db.repositories.user_repository import UserRepository
from app.services.bill_service import BillService
from app.services.building_service import BuildingService
from app.services.dashboard_service import DashboardService
from app.services.lease_service import LeaseService
from app.services.tenant_service import TenantService
from app.services.unit_service import UnitService
from app.services.user_service import UserService

logger = get_logger(__name__)

# (container module, partition-key field) for every document type we persist.
_CONTAINERS = (
    (building_repository.CONTAINER_NAME, building_repository.PARTITION_KEY_FIELD),
    (unit_repository.CONTAINER_NAME, unit_repository.PARTITION_KEY_FIELD),
    (tenant_repository.CONTAINER_NAME, tenant_repository.PARTITION_KEY_FIELD),
    (lease_repository.CONTAINER_NAME, lease_repository.PARTITION_KEY_FIELD),
    (bill_repository.CONTAINER_NAME, bill_repository.PARTITION_KEY_FIELD),
    (user_repository.CONTAINER_NAME, user_repository.PARTITION_KEY_FIELD),
)


async def _build_backends(app: FastAPI) -> dict[str, BaseRepository]:
    """Construct one storage backend per document type, based on settings."""
    settings = get_settings()

    if settings.db_backend == "cosmos":
        from app.db.cosmos_client import CosmosConnection, CosmosRepository

        connection = CosmosConnection(settings)
        await connection.connect()
        app.state.cosmos_connection = connection

        backends: dict[str, BaseRepository] = {}
        for name, pk in _CONTAINERS:
            container = await connection.get_container(name, pk)
            backends[name] = CosmosRepository(container, pk)
        return backends

    if settings.db_backend == "file":
        os.makedirs(settings.data_dir, exist_ok=True)
        return {
            name: JsonFileRepository(pk, os.path.join(settings.data_dir, f"{name}.json"))
            for name, pk in _CONTAINERS
        }

    # Default: in-memory, zero external dependencies.
    return {name: InMemoryRepository(pk) for name, pk in _CONTAINERS}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("startup", app=settings.app_name, db_backend=settings.db_backend)

    backends = await _build_backends(app)

    building_service = BuildingService(BuildingRepository(backends["buildings"]))
    unit_service = UnitService(UnitRepository(backends["units"]), building_service)
    tenant_service = TenantService(
        TenantRepository(backends["tenants"]), building_service, unit_service
    )
    lease_service = LeaseService(
        LeaseRepository(backends["leases"]), building_service, unit_service
    )
    bill_service = BillService(
        BillRepository(backends["bills"]),
        building_service,
        lease_service,
        tenant_service,
        unit_service,
    )
    dashboard_service = DashboardService(
        building_service, unit_service, tenant_service, bill_service
    )
    user_service = UserService(UserRepository(backends["users"]))

    app.state.building_service = building_service
    app.state.unit_service = unit_service
    app.state.tenant_service = tenant_service
    app.state.lease_service = lease_service
    app.state.bill_service = bill_service
    app.state.dashboard_service = dashboard_service
    app.state.user_service = user_service

    yield

    connection = getattr(app.state, "cosmos_connection", None)
    if connection is not None:
        await connection.close()
    logger.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        description="RentWise — landlord rental management (buildings, tenants, rent & utility "
        "bills, contract parsing) on FastAPI + async repositories, JWT, structlog.",
        lifespan=lifespan,
    )
    # CORS: "*" in dev, or a comma-separated allowlist in production.
    raw = settings.cors_origins.strip()
    origins = ["*"] if raw == "*" else [o.strip() for o in raw.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(buildings.router)
    app.include_router(units.router)
    app.include_router(tenants.router)
    app.include_router(leases.router)
    app.include_router(bills.router)
    app.include_router(contracts.router)
    app.include_router(chat.router)
    return app


# Module-level instance for uvicorn (`uvicorn app.main:app`).
app = create_app()
