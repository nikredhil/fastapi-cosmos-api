"""FastAPI dependency providers.

Services are constructed once at startup and stored on ``app.state``; these
providers simply hand them to route handlers.
"""
from __future__ import annotations

from fastapi import Request

from app.services.member_service import MemberService
from app.services.project_service import ProjectService
from app.services.sprint_service import SprintService
from app.services.task_service import TaskService
from app.services.user_service import UserService


def get_user_service(request: Request) -> UserService:
    return request.app.state.user_service


def get_project_service(request: Request) -> ProjectService:
    return request.app.state.project_service


def get_task_service(request: Request) -> TaskService:
    return request.app.state.task_service


def get_member_service(request: Request) -> MemberService:
    return request.app.state.member_service


def get_sprint_service(request: Request) -> SprintService:
    return request.app.state.sprint_service
