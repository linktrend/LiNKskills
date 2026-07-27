"""Test-only helpers for Gateway auth.

Production/non-test paths must use :class:`PlatformClaimsVerifier` from
``linkskills_gateway.auth``. This module retains the retired ``fake.*``
snake_case helper solely so existing unit tests can migrate deliberately.
"""

from __future__ import annotations

import base64
import json
import time
from typing import Any, Mapping

from .auth import AuthError, PlatformClaimsVerifier, mint_platform_token


def mint_fake_token(claims: Mapping[str, Any]) -> str:
    """Retired helper — converts snake_case claims into a fake.* token.

    Not accepted by :class:`PlatformClaimsVerifier`. Prefer
    :func:`mint_platform_token` with canonical AuthClaims.
    """
    payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return f"fake.{encoded}"


def snake_claims_to_platform_claims(claims: Mapping[str, Any]) -> dict[str, Any]:
    """Map legacy snake_case test claims into Platform AuthClaims."""
    now = int(time.time())
    exp = int(claims.get("exp") or (now + 3600))
    issued = max(0, exp - 3600)
    scopes = claims.get("scopes") or ["lskills"]
    if isinstance(scopes, str):
        scopes = [scopes]
    ops = []
    if "skills:read" in scopes or "read" in scopes:
        ops.append("read")
        ops.append("skills:read")
    if "skills:write" in scopes or "execute" in scopes or "skills:write" in scopes:
        ops.extend(["execute", "skills:write"])
    if not ops:
        ops = ["read", "execute", "skills:read", "skills:write"]
    return {
        "claimContractVersion": "1.0.0",
        "actorId": claims.get("actor_id") or claims.get("actorId") or "actor-test",
        "actorKind": claims.get("actor_kind") or claims.get("actorKind") or "agent",
        "runtimeBindingId": claims.get("runtime_binding_id") or "bind-test-1",
        "credentialId": claims.get("credential_id") or claims.get("credentialId") or "cred-test",
        "orgId": claims.get("org_id") or claims.get("orgId") or "org-internal",
        "internal": True,
        "serviceScopes": ["lskills", "linkplatform"],
        "permittedOperations": sorted(set(ops)),
        "issuedAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(issued)),
        "expiresAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(exp)),
        "issuer": "linkplatform-issuer",
        "audience": ["lskills-api"],
        "correlationId": claims.get("correlation_id") or "corr-test-1",
    }


def mint_test_bearer(claims: Mapping[str, Any] | None = None) -> str:
    """Mint a Platform-shaped bearer token for Gateway unit tests."""
    base = {
        "actor_id": "actor-1",
        "actor_kind": "agent",
        "org_id": "org-1",
        "scopes": ["skills:read", "skills:write"],
        "exp": int(time.time()) + 3600,
        "credential_id": "cred-1",
    }
    if claims:
        base.update(dict(claims))
    return mint_platform_token(snake_claims_to_platform_claims(base))


class RejectFakeTokenVerifier(PlatformClaimsVerifier):
    """Explicit alias documenting that fake.* tokens are rejected here."""

    def verify(self, authorization, **kwargs):  # type: ignore[no-untyped-def]
        if authorization and "fake." in authorization:
            raise AuthError(
                "auth_unsupported",
                "fake.* tokens are test-legacy and rejected on PlatformClaimsVerifier",
            )
        return super().verify(authorization, **kwargs)
