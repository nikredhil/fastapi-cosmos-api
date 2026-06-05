"""Backend selector for the chat assistant.

Chooses between the Ollama tool-calling agent and the deterministic rule-based
engine, controlled by the CHAT_BACKEND env var:

    auto   (default) — use Ollama if reachable, otherwise rules
    ollama           — force Ollama (falls back to rules on error)
    rules            — force the rule-based engine

Always returns a reply; it never raises, so the UI can't be broken by a flaky
LLM. The second return value names the backend that actually produced the reply.
"""
from __future__ import annotations

import os

from app.chat import chat_engine, llm_agent
from app.chat.chat_engine import SupportsApi

CHAT_BACKEND = os.getenv("CHAT_BACKEND", "auto").lower()


def respond(
    client: SupportsApi, message: str, history: list[dict[str, str]] | None = None
) -> tuple[str, str]:
    """Return (reply, backend_used) where backend_used is 'ollama' or 'rules'."""
    use_ollama = CHAT_BACKEND == "ollama" or (
        CHAT_BACKEND == "auto" and llm_agent.is_available()
    )

    if use_ollama:
        try:
            return llm_agent.chat(client, message, history=history), "ollama"
        except Exception:  # noqa: BLE001 - degrade gracefully to the rule engine
            return chat_engine.handle(client, message), "rules"

    return chat_engine.handle(client, message), "rules"
