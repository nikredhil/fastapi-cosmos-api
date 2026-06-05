"""Microsoft Entra ID (Azure AD) token validation.

The SPA signs the user in with Microsoft via MSAL and sends the resulting ID
token as a Bearer credential. This module validates that token against
Microsoft's published public keys (RS256 / JWKS): signature, audience (our app
registration's client id), expiry, and issuer. The validated subject (the
account's stable object id) identifies the user throughout the API.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import Settings, get_settings

_bearer = HTTPBearer(auto_error=True)

# Local accounts get a "local:" subject prefix so they never collide with a
# Microsoft object id, and so per-user data partitions stay distinct by source.
_LOCAL_PREFIX = "local:"

# Microsoft v2.0 issuers look like https://login.microsoftonline.com/<tenant-id>/v2.0
# The tenant id varies per account (work tenants + the personal-accounts tenant),
# so we match the shape rather than a single fixed value.
_ISSUER_RE = re.compile(r"^https://login\.microsoftonline\.com/[^/]+/v2\.0$")

# Cache of OIDC signing keys, keyed by `kid`. Populated lazily and refreshed when
# a token presents an unknown key id (e.g. after Microsoft rotates keys).
_jwks_cache: dict[str, dict] = {}


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _fetch_jwks(authority: str) -> dict[str, dict]:
    """Fetch Microsoft's current signing keys, indexed by key id (`kid`)."""
    meta = httpx.get(
        f"{authority.rstrip('/')}/v2.0/.well-known/openid-configuration", timeout=5.0
    )
    meta.raise_for_status()
    jwks_uri = meta.json()["jwks_uri"]
    keys = httpx.get(jwks_uri, timeout=5.0)
    keys.raise_for_status()
    return {k["kid"]: k for k in keys.json().get("keys", []) if "kid" in k}


def _signing_key(kid: str, authority: str) -> dict | None:
    """Return the JWK for `kid`, refreshing the cache once on a miss."""
    if kid in _jwks_cache:
        return _jwks_cache[kid]
    try:
        _jwks_cache.clear()
        _jwks_cache.update(_fetch_jwks(authority))
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise _unauthorized("Unable to fetch Microsoft signing keys") from exc
    return _jwks_cache.get(kid)


def create_access_token(subject: str, settings: Settings) -> str:
    """Mint a local HS256 token for an email/password account."""
    now = datetime.now(timezone.utc)
    claims = {
        "sub": f"{_LOCAL_PREFIX}{subject}",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _validate_local(token: str, settings: Settings) -> str:
    """Validate a token this API issued for a local account."""
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise _unauthorized("Invalid or expired token") from exc
    subject = claims.get("sub")
    if not subject:
        raise _unauthorized("Token missing subject")
    return subject


def _validate_microsoft(token: str, settings: Settings) -> str:
    """Validate a Microsoft (Entra ID) ID token against Microsoft's public keys."""
    if not settings.azure_client_id:
        raise _unauthorized("Microsoft sign-in is not configured (AZURE_CLIENT_ID unset)")

    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except JWTError as exc:
        raise _unauthorized("Malformed token") from exc
    if not kid:
        raise _unauthorized("Token missing key id")

    key = _signing_key(kid, settings.azure_authority)
    if key is None:
        raise _unauthorized("Unknown token signing key")

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.azure_client_id,
            # Issuer is tenant-specific under /common; validated by shape below.
            options={"verify_iss": False},
        )
    except JWTError as exc:
        raise _unauthorized("Invalid or expired token") from exc

    issuer = claims.get("iss", "")
    if not _ISSUER_RE.match(issuer):
        raise _unauthorized("Untrusted token issuer")

    # `oid` is the immutable per-user object id; fall back to `sub` if absent.
    subject = claims.get("oid") or claims.get("sub")
    if not subject:
        raise _unauthorized("Token missing subject")
    return subject


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> str:
    """Return the user's stable id from the bearer token.

    Two token sources are accepted, distinguished by signing algorithm:
    local accounts (HS256, issued by this API) and Microsoft (RS256, Entra ID).
    Raises 401 if the token is missing, malformed, or fails validation.
    """
    token = credentials.credentials
    try:
        alg = jwt.get_unverified_header(token).get("alg")
    except JWTError as exc:
        raise _unauthorized("Malformed token") from exc

    if alg == settings.jwt_algorithm:  # HS256 → a token we issued
        return _validate_local(token, settings)
    return _validate_microsoft(token, settings)
