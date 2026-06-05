"""Microsoft Entra ID (Azure AD) token validation.

The SPA signs the user in with Microsoft via MSAL and sends the resulting ID
token as a Bearer credential. This module validates that token against
Microsoft's published public keys (RS256 / JWKS): signature, audience (our app
registration's client id), expiry, and issuer. The validated subject (the
account's stable object id) identifies the user throughout the API.
"""
from __future__ import annotations

import re

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import Settings, get_settings

_bearer = HTTPBearer(auto_error=True)

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


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> str:
    """Validate the Microsoft ID token and return the user's stable id.

    Raises 401 if the token is missing, malformed, or fails validation.
    """
    if not settings.azure_client_id:
        raise _unauthorized("Microsoft sign-in is not configured (AZURE_CLIENT_ID unset)")

    token = credentials.credentials
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
