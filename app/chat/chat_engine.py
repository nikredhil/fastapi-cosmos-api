"""Rule-based chat assistant for the rental manager.

Parses a landlord's natural-language message, calls the API to fulfil the intent,
and returns a plain-text reply. No external AI service is required — intents are
matched with simple, deterministic rules, which keeps the assistant working even
when no LLM is available.

The engine only depends on an object exposing the ApiClient methods
(``list_buildings``, ``list_units``, ``list_tenants``, ``list_bills``,
``dashboard``), so it can be unit-tested with a lightweight fake.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Protocol

HELP_TEXT = (
    "I can help you manage your rentals. Try:\n"
    "  • *list my buildings*\n"
    "  • *show tenants in Lakeview Apartments*\n"
    "  • *who hasn't paid rent?* / *overdue bills*\n"
    "  • *bills for June* / *this month's summary*\n"
    "  • *how much is outstanding?*"
)


class SupportsApi(Protocol):
    def list_buildings(self) -> list[dict[str, Any]]: ...
    def list_units(self, building_id: str) -> list[dict[str, Any]]: ...
    def list_tenants(self, building_id: str) -> list[dict[str, Any]]: ...
    def list_bills(
        self, building_id: str, period: str | None = ..., status: str | None = ...,
        bill_type: str | None = ...,
    ) -> list[dict[str, Any]]: ...
    def dashboard(self, period: str | None = ...) -> dict[str, Any]: ...


_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9,
    "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _rupees(amount: Any) -> str:
    try:
        return f"₹{int(amount):,}"
    except (ValueError, TypeError):
        return "₹0"


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _find_period(text: str) -> str | None:
    """Pull a 'YYYY-MM' or month-name out of the text, if present."""
    m = re.search(r"\b(20\d{2})-(0[1-9]|1[0-2])\b", text)
    if m:
        return m.group(0)
    lowered = text.lower()
    for name, num in _MONTHS.items():
        if re.search(rf"\b{name}\b", lowered):
            year = datetime.now(timezone.utc).year
            return f"{year}-{num:02d}"
    return None


def _resolve_building(client: SupportsApi, name: str) -> dict[str, Any] | None:
    """Match a building by name (case-insensitive exact, then substring)."""
    name = name.strip().strip("\"'").lower()
    buildings = client.list_buildings()
    for b in buildings:
        if b["name"].lower() == name:
            return b
    for b in buildings:
        if name and name in b["name"].lower():
            return b
    return None


def _all_bills(client: SupportsApi, period: str | None, status: str | None) -> list[dict[str, Any]]:
    """Gather bills across every building, annotated with the building name."""
    out: list[dict[str, Any]] = []
    for b in client.list_buildings():
        for bill in client.list_bills(b["id"], period=period, status=status):
            bill = {**bill, "building_name": b["name"]}
            out.append(bill)
    return out


def _format_bill(bill: dict[str, Any]) -> str:
    who = bill.get("tenant_name") or "—"
    unit = f" ({bill['unit_label']})" if bill.get("unit_label") else ""
    outstanding = int(bill.get("amount", 0)) - int(bill.get("paid_amount", 0))
    return (
        f"  • {who}{unit} — {bill.get('bill_type', 'rent')} {bill.get('period', '')}: "
        f"{_rupees(bill.get('amount'))} due, {_rupees(outstanding)} outstanding "
        f"[{bill.get('status', 'unpaid')}]"
    )


def handle(client: SupportsApi, message: str) -> str:
    """Route a message to an intent handler and return a reply string."""
    text = message.strip()
    if not text:
        return "Say something — type *help* to see what I can do."
    lowered = text.lower()

    if lowered in {"help", "?", "what can you do", "what can you do?"}:
        return HELP_TEXT
    if lowered in {"hi", "hello", "hey", "yo"}:
        return "Hi! I'm your rental assistant. Type *help* for examples."

    # --- overdue / unpaid rent ---
    if any(w in lowered for w in ("overdue", "hasn't paid", "haven't paid", "not paid", "unpaid", "who owes")):
        status = "overdue" if "overdue" in lowered else None
        period = _find_period(text)
        bills = [
            b for b in _all_bills(client, period=period, status=status)
            if b.get("status") in ("overdue", "unpaid", "partial")
        ]
        if not bills:
            return "Everyone's paid up — no outstanding bills. 🎉"
        total = sum(int(b.get("amount", 0)) - int(b.get("paid_amount", 0)) for b in bills)
        lines = "\n".join(_format_bill(b) for b in bills)
        return f"{len(bills)} outstanding bill(s), {_rupees(total)} owed:\n{lines}"

    # --- summary / outstanding / overview ---
    if any(w in lowered for w in ("summary", "overview", "outstanding", "how much", "collected", "status report")):
        period = _find_period(text)
        d = client.dashboard(period=period)
        return (
            f"Summary for {d['period']}:\n"
            f"  • {d['buildings']} building(s), {d['units']} unit(s), "
            f"{d['occupancy_pct']}% occupied\n"
            f"  • {d['active_tenants']} active tenant(s)\n"
            f"  • Expected {_rupees(d['expected'])}, collected {_rupees(d['collected'])}, "
            f"outstanding {_rupees(d['outstanding'])}\n"
            f"  • {len(d['overdue'])} overdue bill(s)"
        )

    # --- who is <name> / find tenant <name> ---
    m = re.search(
        r"(?:who\s+is|who'?s|find\s+tenant|about\s+tenant|details?\s+(?:for|of))\s+(.+)$",
        text,
        re.IGNORECASE,
    )
    if m:
        who = m.group(1).strip().strip("\"'?.").lower()
        for b in client.list_buildings():
            units = {u["id"]: u.get("label") for u in client.list_units(b["id"])}
            for t in client.list_tenants(b["id"]):
                if who in t["name"].lower():
                    unit = units.get(t.get("unit_id"))
                    bills = client.list_bills(b["id"], status=None)
                    owed = sum(
                        int(x.get("amount", 0)) - int(x.get("paid_amount", 0))
                        for x in bills
                        if x.get("tenant_id") == t["id"]
                        and x.get("status") in ("unpaid", "partial", "overdue")
                    )
                    parts = [f"*{t['name']}* — tenant in {b['name']}"]
                    if unit:
                        parts.append(f"unit {unit}")
                    if t.get("phone"):
                        parts.append(t["phone"])
                    if t.get("deposit"):
                        parts.append(f"deposit {_rupees(t['deposit'])}")
                    line = ", ".join(parts) + "."
                    if owed > 0:
                        line += f" Outstanding: {_rupees(owed)}."
                    return line
        return f"I couldn't find a tenant named '{m.group(1).strip()}'."

    # --- tenants in a specific building ---
    m = re.search(r"tenants?\s+(?:in|at|for|of)\s+(.+)$", text, re.IGNORECASE)
    if m:
        building = _resolve_building(client, m.group(1))
        if building is None:
            return f"I couldn't find a building matching '{m.group(1).strip()}'."
        tenants = client.list_tenants(building["id"])
        if not tenants:
            return f"{building['name']} has no tenants yet."
        lines = "\n".join(
            f"  • {t['name']}" + (f" — {t.get('phone')}" if t.get("phone") else "")
            for t in tenants
        )
        return f"Tenants in {building['name']}:\n{lines}"

    # --- all tenants ---
    if "tenant" in lowered:
        chunks, total = [], 0
        for b in client.list_buildings():
            tenants = client.list_tenants(b["id"])
            if tenants:
                total += len(tenants)
                names = ", ".join(t["name"] for t in tenants)
                chunks.append(f"  • {b['name']}: {names}")
        if total == 0:
            return "You have no tenants yet."
        return f"{total} tenant(s):\n" + "\n".join(chunks)

    # --- bills for a month ---
    if "bill" in lowered or "rent" in lowered:
        period = _find_period(text) or _current_period()
        bills = _all_bills(client, period=period, status=None)
        if not bills:
            return f"No bills found for {period}. Generate them from the Rent & Bills page."
        total = sum(int(b.get("amount", 0)) for b in bills)
        paid = sum(int(b.get("paid_amount", 0)) for b in bills)
        lines = "\n".join(_format_bill(b) for b in bills[:20])
        more = "" if len(bills) <= 20 else f"\n  …and {len(bills) - 20} more"
        return (
            f"Bills for {period} — {_rupees(total)} billed, {_rupees(paid)} collected:\n"
            f"{lines}{more}"
        )

    # --- list buildings ---
    if "building" in lowered or "propert" in lowered or lowered in {"list", "show all"}:
        buildings = client.list_buildings()
        if not buildings:
            return "You have no buildings yet. Add one from the Buildings page."
        lines = []
        for b in buildings:
            units = client.list_units(b["id"])
            occ = sum(1 for u in units if u.get("status") == "occupied")
            loc = f" — {b['city']}" if b.get("city") else ""
            lines.append(f"  • {b['name']}{loc} ({occ}/{len(units)} units occupied)")
        return "Your buildings:\n" + "\n".join(lines)

    return "I'm not sure how to help with that. Type *help* to see what I can do."
