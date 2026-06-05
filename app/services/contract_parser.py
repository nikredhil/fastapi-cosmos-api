"""Parse an uploaded rental-contract photo into structured fields with Claude.

Uses the Anthropic Python SDK's vision support: the image is sent as a base64
content block and the model is forced to call a single tool whose schema is the
set of fields we want, guaranteeing structured JSON back. When no API key is
configured the parser is disabled and the UI falls back to manual entry.
"""
from __future__ import annotations

import base64
from typing import Any

from app.core.config import Settings, get_settings

# Tool input schema = the fields we extract. Kept flat and simple; the model
# fills what it can read and leaves the rest null.
CONTRACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "tenant_name": {"type": ["string", "null"], "description": "Full name of the tenant"},
        "tenant_phone": {"type": ["string", "null"], "description": "Tenant phone number"},
        "tenant_email": {"type": ["string", "null"], "description": "Tenant email, if present"},
        "unit_label": {
            "type": ["string", "null"],
            "description": "Flat/unit identifier, e.g. 'A-101' or 'Flat 3B'",
        },
        "monthly_rent": {
            "type": ["integer", "null"],
            "description": "Monthly rent in INR (rupees), as an integer",
        },
        "deposit": {
            "type": ["integer", "null"],
            "description": "Security deposit in INR (rupees), as an integer",
        },
        "start_date": {"type": ["string", "null"], "description": "Lease start date, ISO YYYY-MM-DD"},
        "end_date": {"type": ["string", "null"], "description": "Lease end date, ISO YYYY-MM-DD"},
        "rent_due_day": {
            "type": ["integer", "null"],
            "description": "Day of the month rent is due (1-31)",
        },
        "terms_summary": {
            "type": ["string", "null"],
            "description": "A 1-2 sentence summary of notable terms (notice period, lock-in, etc.)",
        },
    },
    "additionalProperties": False,
}

_FIELDS = list(CONTRACT_SCHEMA["properties"].keys())

_PROMPT = (
    "You are reading a scanned/photographed residential rental agreement from India. "
    "Extract the fields and call the record_contract tool exactly once. "
    "Convert any rent/deposit amounts to plain integers in INR (drop ₹, commas, and the word "
    "'rupees'). Use ISO dates (YYYY-MM-DD). If a field is not clearly stated, set it to null — "
    "do not guess."
)


def is_enabled(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    return bool(settings.anthropic_api_key)


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _empty() -> dict[str, Any]:
    return {field: None for field in _FIELDS}


def parse_contract_image(
    image_bytes: bytes, media_type: str, settings: Settings | None = None
) -> dict[str, Any]:
    """Return a dict of extracted fields plus a ``parsed`` flag.

    Never raises — on any error (no key, transport failure) it returns empty
    fields with ``parsed=False`` so the caller can fall back to manual entry.
    """
    settings = settings or get_settings()
    if not settings.anthropic_api_key:
        return {**_empty(), "parsed": False, "error": "Contract parsing is not configured."}

    try:
        from anthropic import Anthropic  # imported lazily so the app boots without the SDK

        client = Anthropic(api_key=settings.anthropic_api_key)
        data = base64.standard_b64encode(image_bytes).decode("ascii")
        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            tools=[
                {
                    "name": "record_contract",
                    "description": "Record the rental-contract fields extracted from the image.",
                    "input_schema": CONTRACT_SCHEMA,
                }
            ],
            tool_choice={"type": "tool", "name": "record_contract"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": data,
                            },
                        },
                        {"type": "text", "text": _PROMPT},
                    ],
                }
            ],
        )
    except Exception as exc:  # noqa: BLE001 - degrade gracefully to manual entry
        return {**_empty(), "parsed": False, "error": str(exc)}

    raw: dict[str, Any] = {}
    for block in message.content:
        if getattr(block, "type", None) == "tool_use":
            raw = dict(block.input)  # type: ignore[arg-type]
            break

    result = _empty()
    for field in _FIELDS:
        result[field] = raw.get(field)
    result["monthly_rent"] = _coerce_int(result.get("monthly_rent"))
    result["deposit"] = _coerce_int(result.get("deposit"))
    result["rent_due_day"] = _coerce_int(result.get("rent_due_day"))
    result["parsed"] = True
    result["error"] = None
    return result


__all__ = ["parse_contract_image", "is_enabled", "CONTRACT_SCHEMA"]
