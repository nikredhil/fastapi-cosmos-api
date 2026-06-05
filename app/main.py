"""Application entry point: lifespan wiring, middleware, router registration."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os

from app.api.routers import chat, health, members, projects, sprints, tasks
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.repositories import (
    member_repository,
    project_repository,
    sprint_repository,
    task_repository,
)
from app.db.repositories.base import BaseRepository
from app.db.repositories.file_store import JsonFileRepository
from app.db.repositories.member_repository import MemberRepository
from app.db.repositories.memory import InMemoryRepository
from app.db.repositories.project_repository import ProjectRepository
from app.db.repositories.sprint_repository import SprintRepository
from app.db.repositories.task_repository import TaskRepository
from app.services.member_service import MemberService
from app.services.project_service import ProjectService
from app.services.sprint_service import SprintService
from app.services.task_service import TaskService

logger = get_logger(__name__)

# (container module, partition-key field) for every document type we persist.
_CONTAINERS = (
    (project_repository.CONTAINER_NAME, project_repository.PARTITION_KEY_FIELD),
    (task_repository.CONTAINER_NAME, task_repository.PARTITION_KEY_FIELD),
    (member_repository.CONTAINER_NAME, member_repository.PARTITION_KEY_FIELD),
    (sprint_repository.CONTAINER_NAME, sprint_repository.PARTITION_KEY_FIELD),
)


async def _build_backends(app: FastAPI) -> dict[str, BaseRepository]:
    """Construct one storage backend per document type, based on settings.

    Returns a dict keyed by container name (projects/tasks/members/sprints).
    """
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

    project_service = ProjectService(ProjectRepository(backends["projects"]))
    member_service = MemberService(MemberRepository(backends["members"]), project_service)
    sprint_service = SprintService(SprintRepository(backends["sprints"]), project_service)
    task_service = TaskService(
        TaskRepository(backends["tasks"]), project_service, member_service
    )
    app.state.project_service = project_service
    app.state.member_service = member_service
    app.state.sprint_service = sprint_service
    app.state.task_service = task_service

    yield

    connection = getattr(app.state, "cosmos_connection", None)
    if connection is not None:
        await connection.close()
    logger.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Task/Project Tracker — FastAPI + async Cosmos DB repositories, JWT, structlog.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(projects.router)
    app.include_router(tasks.router)
    app.include_router(members.router)
    app.include_router(sprints.router)
    app.include_router(chat.router)
    return app


# Module-level instance for uvicorn (`uvicorn app.main:app`).
app = create_app()
