"""Test-only helpers for Gateway auth.

Production/non-test paths must use :class:`PlatformClaimsVerifier` with an
injected Platform-approved cryptographic authenticator. This module may mint
unsigned local-test tokens and test-only signed tokens; it must not be used as
the production Gateway/MCP default verifier.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Mapping, Optional

from .auth import (
    CLAIM_CONTRACT_VERSION,
    AuthError,
    AuthenticatedToken,
    LocalUnsignedClaimsVerifier,
    PlatformClaimsVerifier,
    PlatformTokenAuthenticator,
)


# Explicit test-only HMAC material — NOT a Platform production signing key.
LOCAL_TEST_HMAC_SECRET = b"linkskills-local-test-hmac-not-a-platform-key"


def mint_fake_token(claims: Mapping[str, Any]) -> str:
    """Retired helper — emits a ``fake.*`` token rejected by all verifiers."""
    payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return f"fake.{encoded}"


def mint_platform_token(claims: Mapping[str, Any]) -> str:
    """Mint an unsigned ``platform.<b64>`` token for local-test mode only.

    Production ``PlatformClaimsVerifier`` rejects these tokens.
    """
    payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return f"platform.{encoded}"


def snake_claims_to_platform_claims(claims: Mapping[str, Any]) -> dict[str, Any]:
    """Map legacy snake_case *test* claims into frozen Platform AuthClaims.

    Not accepted by the production verifier directly. Used only to mint tokens
    in unit tests.
    """
    now = int(time.time())
    exp = int(claims.get("exp") or (now + 3600))
    issued = max(0, exp - 3600)
    scopes = claims.get("scopes") or ["lskills"]
    if isinstance(scopes, str):
        scopes = [scopes]
    ops: list[str] = []
    if "skills:read" in scopes or "read" in scopes:
        ops.extend(["read", "skills:read"])
    if "skills:write" in scopes or "execute" in scopes:
        ops.extend(["execute", "skills:write", "skills:run", "skills:feedback"])
    if not ops:
        ops = [
            "read",
            "execute",
            "skills:read",
            "skills:write",
            "skills:run",
            "skills:feedback",
        ]

    actor_kind = str(claims.get("actor_kind") or claims.get("actorKind") or "service")
    if actor_kind == "agent":
        actor_kind = "service"

    if "permittedOperations" in claims:
        permitted = list(claims["permittedOperations"] or [])
    else:
        permitted = sorted(set(ops))

    return {
        "claimContractVersion": CLAIM_CONTRACT_VERSION,
        "actorId": claims.get("actor_id") or claims.get("actorId") or "actor-test",
        "actorKind": actor_kind,
        "runtimeBindingId": claims.get("runtime_binding_id")
        or claims.get("runtimeBindingId")
        or "bind-test-1",
        "credentialId": claims.get("credential_id")
        or claims.get("credentialId")
        or "cred-test",
        "orgId": claims.get("org_id") or claims.get("orgId") or "org-internal",
        "internal": True,
        "serviceScopes": list(claims.get("serviceScopes") or ["lskills", "linkplatform"]),
        "permittedOperations": permitted,
        "issuedAt": claims.get("issuedAt")
        or time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(issued)),
        "expiresAt": claims.get("expiresAt")
        or time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(exp)),
        "issuer": claims.get("issuer") or "linkplatform-issuer",
        "audience": list(claims.get("audience") or ["lskills-api"]),
        "correlationId": claims.get("correlation_id")
        or claims.get("correlationId")
        or "corr-test-1",
    }


def mint_test_bearer(claims: Mapping[str, Any] | None = None) -> str:
    """Mint an unsigned Platform-shaped bearer for ``LocalUnsignedClaimsVerifier``."""
    base = {
        "actor_id": "actor-1",
        "actor_kind": "service",
        "org_id": "org-1",
        "scopes": ["skills:read", "skills:write"],
        "exp": int(time.time()) + 3600,
        "credential_id": "cred-1",
    }
    if claims:
        base.update(dict(claims))
    return mint_platform_token(snake_claims_to_platform_claims(base))


class LocalTestHmacAuthenticator:
    """Test-only HMAC authenticator (not Platform production key material).

    Token format: ``platform.sig.v1.<payload_b64url>.<mac_b64url>``
    """

    def __init__(
        self,
        secret: bytes = LOCAL_TEST_HMAC_SECRET,
        *,
        credential_status_by_id: Optional[Mapping[str, str]] = None,
        default_credential_status: str = "active",
    ) -> None:
        self.secret = secret
        self.credential_status_by_id = dict(credential_status_by_id or {})
        self.default_credential_status = default_credential_status

    def mint(self, claims: Mapping[str, Any]) -> str:
        payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
        mac = hmac.new(self.secret, payload, hashlib.sha256).digest()
        mac_b64 = base64.urlsafe_b64encode(mac).decode("ascii").rstrip("=")
        return f"platform.sig.v1.{payload_b64}.{mac_b64}"

    def authenticate(self, token: str) -> AuthenticatedToken:
        if not token.startswith("platform.sig.v1."):
            raise AuthError(
                "auth_unsupported",
                "LocalTestHmacAuthenticator accepts only platform.sig.v1.* tokens",
            )
        parts = token.split(".")
        if len(parts) != 5:
            raise AuthError("auth_malformed", "Malformed platform.sig.v1 token")
        payload_b64, mac_b64 = parts[3], parts[4]
        try:
            payload = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4))
            mac = base64.urlsafe_b64decode(mac_b64 + "=" * (-len(mac_b64) % 4))
        except ValueError as exc:
            raise AuthError("auth_malformed", "Malformed platform.sig.v1 encoding") from exc
        expected = hmac.new(self.secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected):
            raise AuthError("auth_signature_invalid", "HMAC signature verification failed")
        try:
            claims = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise AuthError("auth_malformed", "Signed payload is not JSON") from exc
        if not isinstance(claims, dict):
            raise AuthError("auth_malformed", "Signed payload must be an object")
        cred_id = str(claims.get("credentialId") or "")
        status = self.credential_status_by_id.get(cred_id, self.default_credential_status)
        return AuthenticatedToken(claims=claims, credential_status=status)


def mint_signed_test_bearer(
    claims: Mapping[str, Any] | None = None,
    *,
    authenticator: Optional[LocalTestHmacAuthenticator] = None,
) -> str:
    """Mint a cryptographically signed test bearer for production-path tests."""
    auth = authenticator or LocalTestHmacAuthenticator()
    base = {
        "actor_id": "actor-1",
        "actor_kind": "service",
        "org_id": "org-1",
        "scopes": ["skills:read", "skills:write"],
        "exp": int(time.time()) + 3600,
        "credential_id": "cred-1",
    }
    if claims:
        base.update(dict(claims))
    return auth.mint(snake_claims_to_platform_claims(base))


def production_test_verifier(
    *,
    authenticator: Optional[LocalTestHmacAuthenticator] = None,
    **policy_kwargs: Any,
) -> PlatformClaimsVerifier:
    """Build a production-path verifier with the local-test HMAC authenticator."""
    return PlatformClaimsVerifier(
        authenticator=authenticator or LocalTestHmacAuthenticator(),
        **policy_kwargs,
    )


class RejectFakeTokenVerifier(LocalUnsignedClaimsVerifier):
    """Explicit local-test alias documenting that fake.* tokens are rejected."""

    def verify(self, authorization, **kwargs):  # type: ignore[no-untyped-def]
        if authorization and "fake." in authorization:
            raise AuthError(
                "auth_unsupported",
                "fake.* tokens are test-legacy and rejected",
            )
        return super().verify(authorization, **kwargs)


# Type check aid: LocalTestHmacAuthenticator satisfies the Protocol.
_: PlatformTokenAuthenticator = LocalTestHmacAuthenticator()
