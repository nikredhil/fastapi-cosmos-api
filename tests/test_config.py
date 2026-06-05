"""Tests for environment-aware settings validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import DEFAULT_JWT_SECRET, Settings


def test_local_defaults_are_valid() -> None:
    settings = Settings(environment="local")
    assert settings.jwt_secret == DEFAULT_JWT_SECRET
    assert settings.cors_origins == ["*"]


def test_default_secret_rejected_outside_local() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(environment="prod", cors_origins=["https://app.example.com"])


def test_wildcard_cors_rejected_outside_local() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(environment="prod", jwt_secret="a-real-secret", cors_origins=["*"])


def test_prod_with_explicit_config_is_valid() -> None:
    settings = Settings(
        environment="prod",
        jwt_secret="a-real-secret",
        cors_origins=["https://app.example.com"],
    )
    assert settings.cors_origins == ["https://app.example.com"]


def test_cosmos_backend_requires_credentials() -> None:
    with pytest.raises(ValidationError, match="COSMOS_ENDPOINT"):
        Settings(db_backend="cosmos")


def test_cosmos_backend_with_credentials_is_valid() -> None:
    settings = Settings(
        db_backend="cosmos",
        cosmos_endpoint="https://acct.documents.azure.com:443/",
        cosmos_key="secret-key",
    )
    assert settings.cosmos_endpoint is not None


def test_cors_origins_parses_comma_separated_string() -> None:
    settings = Settings(
        environment="prod",
        jwt_secret="a-real-secret",
        cors_origins="https://a.example.com, https://b.example.com",
    )
    assert settings.cors_origins == ["https://a.example.com", "https://b.example.com"]
