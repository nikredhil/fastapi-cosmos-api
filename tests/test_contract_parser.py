"""Tests for the contract image parser — no real Anthropic call is made."""
from __future__ import annotations

import sys
import types

from app.core.config import Settings
from app.services import contract_parser


def test_disabled_without_key() -> None:
    settings = Settings(anthropic_api_key=None)
    assert contract_parser.is_enabled(settings) is False
    result = contract_parser.parse_contract_image(b"\x89PNG", "image/png", settings)
    assert result["parsed"] is False
    assert result["tenant_name"] is None


def test_parse_with_mocked_client(monkeypatch) -> None:
    # A fake tool_use block the model "returns".
    block = types.SimpleNamespace(
        type="tool_use",
        input={
            "tenant_name": "Rohit Sharma",
            "monthly_rent": "24,000",
            "deposit": 48000,
            "rent_due_day": "5",
            "unit_label": "A-101",
            "start_date": "2026-01-01",
        },
    )
    message = types.SimpleNamespace(content=[block])

    class FakeMessages:
        def create(self, **kwargs):
            return message

    class FakeAnthropic:
        def __init__(self, *a, **k):
            self.messages = FakeMessages()

    fake_module = types.ModuleType("anthropic")
    fake_module.Anthropic = FakeAnthropic
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    settings = Settings(anthropic_api_key="sk-test", anthropic_model="claude-opus-4-8")
    result = contract_parser.parse_contract_image(b"img-bytes", "image/png", settings)

    assert result["parsed"] is True
    assert result["tenant_name"] == "Rohit Sharma"
    assert result["monthly_rent"] == 24000  # coerced from "24,000"
    assert result["deposit"] == 48000
    assert result["rent_due_day"] == 5
    assert result["error"] is None
