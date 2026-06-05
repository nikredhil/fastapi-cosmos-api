"""Application entry point: lifespan wiring, middleware, router registration."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import chat, health, projects, tasks
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.repositories import project_repository, task_repository
from app.db.repositories.base import BaseRepository
from app.db.repositories.memory import InMemoryRepository
from app.db.repositories.project_repository import ProjectRepository
from app.db.repositories.task_repository import TaskRepository
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

logger = get_logger(__name__)


async def _build_backends(app: FastAPI) -> tuple[BaseRepository, BaseRepository]:
    """Construct the storage backends for projects and tasks based on settings."""
    settings = get_settings()

    if settings.db_backend == "cosmos":
        from app.db.cosmos_client import CosmosConnection, CosmosRepository

        connection = CosmosConnection(settings)
        await connection.connect()
        app.state.cosmos_connection = connection

        projects_container = await connection.get_container(
            project_repository.CONTAINER_NAME, project_repository.PARTITION_KEY_FIELD
        )
        tasks_container = await connection.get_container(
            task_repository.CONTAINER_NAME, task_repository.PARTITION_KEY_FIELD
        )
        return (
            CosmosRepository(projects_container, project_repository.PARTITION_KEY_FIELD),
            CosmosRepository(tasks_container, task_repository.PARTITION_KEY_FIELD),
        )

    # Default: in-memory, zero external dependencies.
    return (
        InMemoryRepository(project_repository.PARTITION_KEY_FIELD),
        InMemoryRepository(task_repository.PARTITION_KEY_FIELD),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("startup", app=settings.app_name, db_backend=settings.db_backend)

    projects_backend, tasks_backend = await _build_backends(app)

    project_service = ProjectService(ProjectRepository(projects_backend))
    task_service = TaskService(TaskRepository(tasks_backend), project_service)
    app.state.project_service = project_service
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
    app.include_router(chat.router)
    return app


# Module-level instance for uvicorn (`uvicorn app.main:app`).
app = create_app()
