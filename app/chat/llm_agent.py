"""Ollama-backed tool-calling assistant for the rental manager.

The LLM is given a set of read tools (buildings, tenants, bills, summary). It
decides which to call; this module executes the calls against the API, feeds the
results back, and loops until the model produces a final answer.

Uses Ollama's HTTP API directly (no extra dependency). Works with any
tool-capable model — set OLLAMA_MODEL (e.g. "llama3.2", "gpt-oss:120b-cloud").
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx

from app.chat.chat_engine import SupportsApi, _resolve_building

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
MAX_STEPS = 6

SYSTEM_PROMPT = (
    "You are an assistant for a landlord's rental-management app. The signed-in user owns "
    "buildings; each building has units (flats), tenants, and monthly bills (rent, water, "
    "electricity, maintenance). All amounts are in Indian rupees (₹).\n"
    "ALWAYS use the tools to answer questions about the user's buildings, tenants, or bills — "
    "never answer from general knowledge, and never invent names, amounts, or counts. For "
    "questions about who owes money or what's late, call overdue_bills. For portfolio-wide "
    "numbers (occupancy, collected vs outstanding), call monthly_summary. To answer 'who is "
    "<name>?' call list_tenants for the relevant building(s) and summarise that tenant's unit, "
    "rent status, and contact.\n"
    "NEVER show internal IDs or UUIDs to the user — refer to units by their label (e.g. 'A-101') "
    "and buildings by name. If a value looks like a long random string, omit it.\n"
    "Bill status is one of: unpaid, partial, paid, overdue. Keep replies concise and friendly, "
    "and format money with the ₹ symbol."
)

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_buildings",
            "description": "List all of the landlord's buildings with unit counts.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tenants",
            "description": "List the tenants in a specific building.",
            "parameters": {
                "type": "object",
                "properties": {"building_name": {"type": "string"}},
                "required": ["building_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "overdue_bills",
            "description": (
                "List every outstanding (unpaid/partial/overdue) bill across all buildings. "
                "Use for 'who hasn't paid rent?' or 'what's overdue?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "Optional month, e.g. 2026-06"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "monthly_summary",
            "description": (
                "Portfolio KPIs for a month: occupancy, expected vs collected vs outstanding, "
                "and overdue count."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "Optional month, e.g. 2026-06"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_bills",
            "description": "List bills in a building, optionally filtered by month and/or status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "building_name": {"type": "string"},
                    "period": {"type": "string", "description": "Month, e.g. 2026-06"},
                    "status": {
                        "type": "string",
                        "enum": ["unpaid", "partial", "paid", "overdue"],
                    },
                },
                "required": ["building_name"],
            },
        },
    },
]


def _bill_brief(bill: dict[str, Any]) -> dict[str, Any]:
    return {
        "tenant": bill.get("tenant_name"),
        "unit": bill.get("unit_label"),
        "type": bill.get("bill_type"),
        "period": bill.get("period"),
        "amount": bill.get("amount"),
        "paid": bill.get("paid_amount"),
        "status": bill.get("status"),
    }


def execute_tool(client: SupportsApi, name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Run one tool call against the API. Returns a JSON-serializable result."""
    if name == "list_buildings":
        out = []
        for b in client.list_buildings():
            units = client.list_units(b["id"])
            out.append(
                {
                    "name": b["name"],
                    "city": b.get("city"),
                    "units": len(units),
                    "occupied": sum(1 for u in units if u.get("status") == "occupied"),
                }
            )
        return {"buildings": out}

    if name == "monthly_summary":
        return client.dashboard(period=args.get("period"))

    if name == "overdue_bills":
        period = args.get("period")
        matches = []
        for b in client.list_buildings():
            for bill in client.list_bills(b["id"], period=period):
                if bill.get("status") in ("unpaid", "partial", "overdue"):
                    matches.append({**_bill_brief(bill), "building": b["name"]})
        return {"outstanding": matches}

    if name == "list_tenants":
        building = _resolve_building(client, args.get("building_name", ""))
        if building is None:
            return {"error": f"No building matching '{args.get('building_name', '')}'."}
        units = {u["id"]: u.get("label") for u in client.list_units(building["id"])}
        tenants = client.list_tenants(building["id"])
        return {
            "building": building["name"],
            "tenants": [
                {
                    "name": t["name"],
                    "phone": t.get("phone"),
                    "email": t.get("email"),
                    "unit": units.get(t.get("unit_id")),
                    "deposit": t.get("deposit"),
                    "status": t.get("status"),
                }
                for t in tenants
            ],
        }

    if name == "list_bills":
        building = _resolve_building(client, args.get("building_name", ""))
        if building is None:
            return {"error": f"No building matching '{args.get('building_name', '')}'."}
        bills = client.list_bills(
            building["id"], period=args.get("period"), status=args.get("status")
        )
        return {"building": building["name"], "bills": [_bill_brief(b) for b in bills]}

    return {"error": f"Unknown tool '{name}'."}


def is_available(host: str = OLLAMA_HOST, timeout: float = 1.5) -> bool:
    """Return True if an Ollama server is reachable."""
    try:
        resp = httpx.get(f"{host.rstrip('/')}/api/tags", timeout=timeout)
        return resp.status_code == 200
    except Exception:  # noqa: BLE001 - any failure means "not available"
        return False


def _ollama_chat(messages: list[dict[str, Any]], model: str, host: str) -> dict[str, Any]:
    resp = httpx.post(
        f"{host.rstrip('/')}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "tools": TOOLS,
            "stream": False,
            "options": {"temperature": 0.3},
        },
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()["message"]


def chat(
    client: SupportsApi,
    message: str,
    history: list[dict[str, str]] | None = None,
    model: str = OLLAMA_MODEL,
    host: str = OLLAMA_HOST,
) -> str:
    """Run the tool-calling loop and return the assistant's final reply.

    Raises on transport errors so the caller can fall back to the rule engine.
    """
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history or []:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    for _ in range(MAX_STEPS):
        assistant_msg = _ollama_chat(messages, model, host)
        tool_calls = assistant_msg.get("tool_calls") or []

        if not tool_calls:
            return assistant_msg.get("content", "").strip() or "(no response)"

        messages.append(assistant_msg)
        for call in tool_calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            raw_args = fn.get("arguments", {})
            args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
            result = execute_tool(client, name, args)
            messages.append(
                {"role": "tool", "tool_name": name, "content": json.dumps(result)}
            )

    return "I wasn't able to complete that in a reasonable number of steps — please rephrase."
