"""Chat assistant endpoint.

Runs the assistant server-side and returns its reply. The assistant fulfils
requests by calling this same API as the signed-in user (reusing its bearer
token), so all per-user isolation and validation are enforced by the normal
project/task routes. The (synchronous) assistant runs in a threadpool so it
never blocks the event loop.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.chat.api_client import ApiClient
from app.chat.assistant import respond
from app.core.security import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])
_bearer = HTTPBearer(auto_error=True)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    backend: str = Field(description="Which assistant backend answered: 'ollama' or 'rules'")


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    user: str = Depends(get_current_user),
) -> ChatResponse:
    client = ApiClient(base_url=str(request.base_url), token=credentials.credentials)
    history = [{"role": m.role, "content": m.content} for m in body.history]
    reply, backend = await run_in_threadpool(respond, client, body.message, history)
    return ChatResponse(reply=reply, backend=backend)
