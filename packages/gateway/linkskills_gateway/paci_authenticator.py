"""PACI JWT ``PlatformTokenAuthenticator`` for LiNKskills Gateway.

Wire via::

    LINKSKILLS_PLATFORM_AUTHENTICATOR=\\
      linkskills_gateway.paci_authenticator:build_paci_authenticator_from_environ

**Evidence class:** implemented but not proven against frozen Platform PACI
service (envelope ``platform.auth-token-envelope/0.1.3-draft``).
"""

from __future__ import annotations

import os
from typing import Any, Callable, Mapping, Optional, Sequence

from .auth import (
    AuthConfigurationError,
    AuthError,
    AuthenticatedToken,
    HIGH_RISK_WRITE_OPERATIONS,
)
from .introspection import (
    ClientAssertionSigner,
    IntrospectionClient,
    StubClientAssertionSigner,
)
from .jwks import CachedJwksClient, JwksKeyProvider, validate_issuer_identifier
from .paci_jwt import PaciJwtVerifier
from .paci_types import (
    EVIDENCE_STATUS_NOT_PROVEN,
    PACI_ENVELOPE_CONTRACT,
)


# Environment variable names (documented for operators / canary fragments).
ENV_PACI_ISSUER = "LINKSKILLS_PACI_ISSUER"
ENV_PACI_JWKS_URI = "LINKSKILLS_PACI_JWKS_URI"
ENV_PACI_AUDIENCE = "LINKSKILLS_PACI_AUDIENCE"
ENV_PACI_REQUIRED_SERVICE_SCOPES = "LINKSKILLS_PACI_REQUIRED_SERVICE_SCOPES"
ENV_PACI_INTROSPECTION_URL = "LINKSKILLS_PACI_INTROSPECTION_URL"
ENV_PACI_INTROSPECTION_CLIENT_ID = "LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID"
ENV_PLATFORM_AUTHENTICATOR = "LINKSKILLS_PLATFORM_AUTHENTICATOR"

DEFAULT_AUDIENCE = "lskills-api"
DEFAULT_SERVICE_SCOPE = "lskills"


class PaciJwtAuthenticator:
    """PlatformTokenAuthenticator backed by PACI ES256 + optional introspection.

    ``authenticate(token)`` performs JWT/JWKS/AuthClaims verification.
    High-risk mutating writes must call ``authenticate_for_operation`` (or
    ``require_introspection``) so RFC 7662 active checks run fail-closed.

    Marked: implemented but not proven against frozen Platform PACI service.
    """

    evidence_status = EVIDENCE_STATUS_NOT_PROVEN
    envelope_contract = PACI_ENVELOPE_CONTRACT

    def __init__(
        self,
        *,
        issuer: str,
        audiences: Sequence[str],
        jwks: JwksKeyProvider,
        introspection: Optional[IntrospectionClient] = None,
        required_service_scopes: Optional[Sequence[str]] = None,
        now_fn: Optional[Callable[[], float]] = None,
        high_risk_operations: Optional[frozenset[str]] = None,
    ) -> None:
        validate_issuer_identifier(issuer)
        self.issuer = issuer.strip()
        self.audiences = [str(a).strip() for a in audiences if str(a).strip()]
        if not self.audiences:
            raise AuthConfigurationError("PACI audiences must be non-empty")
        self.required_service_scopes = frozenset(
            str(s).strip()
            for s in (required_service_scopes or (DEFAULT_SERVICE_SCOPE,))
            if str(s).strip()
        )
        self._verifier = PaciJwtVerifier(
            issuer=self.issuer,
            audiences=self.audiences,
            jwks=jwks,
            now_fn=now_fn,
        )
        self._introspection = introspection
        self._high_risk = high_risk_operations or HIGH_RISK_WRITE_OPERATIONS

    def authenticate(self, token: str) -> AuthenticatedToken:
        """Verify PACI JWT authenticity and return AuthClaims (+ active status).

        Does **not** call introspection. Use ``authenticate_for_operation`` for
        high-risk writes.
        """
        verified = self._verifier.verify(token)
        self._check_service_scopes(verified.claims)
        return AuthenticatedToken(
            claims=verified.claims,
            credential_status="active",
            actor_lifecycle_state="active",
            binding_state="active",
        )

    def authenticate_for_operation(
        self,
        token: str,
        *,
        operation: Optional[str] = None,
    ) -> AuthenticatedToken:
        """Authenticate; introspect when ``operation`` is a high-risk write."""
        verified = self._verifier.verify(token)
        self._check_service_scopes(verified.claims)
        if operation and operation in self._high_risk:
            self.require_introspection(
                token,
                jti=verified.jti,
                expected_sub=verified.sub,
                expected_credential_id=str(verified.claims.get("credentialId") or ""),
                expected_runtime_binding_id=str(
                    verified.claims.get("runtimeBindingId") or ""
                ),
            )
        return AuthenticatedToken(
            claims=verified.claims,
            credential_status="active",
            actor_lifecycle_state="active",
            binding_state="active",
        )

    def require_introspection(
        self,
        token: str,
        *,
        jti: str,
        expected_sub: Optional[str] = None,
        expected_credential_id: Optional[str] = None,
        expected_runtime_binding_id: Optional[str] = None,
    ) -> None:
        """Fail-closed introspection gate for high-risk writes."""
        if self._introspection is None:
            raise AuthError(
                "introspection_unavailable",
                "High-risk write requires PACI introspection but no client configured "
                f"({ENV_PACI_INTROSPECTION_URL})",
            )
        self._introspection.require_active(
            token,
            jti=jti,
            expected_sub=expected_sub,
            expected_credential_id=expected_credential_id or None,
            expected_runtime_binding_id=expected_runtime_binding_id or None,
        )

    def is_high_risk(self, operation: Optional[str]) -> bool:
        return bool(operation) and operation in self._high_risk

    def _check_service_scopes(self, claims: Mapping[str, Any]) -> None:
        scopes = claims.get("serviceScopes")
        if not isinstance(scopes, list):
            raise AuthError("auth_invalid", "AuthClaims serviceScopes must be an array")
        have = {str(s).strip() for s in scopes}
        if "*" in have:
            return
        missing = sorted(self.required_service_scopes - have)
        if missing:
            raise AuthError(
                "auth_forbidden",
                "Missing required service scope(s): " + ", ".join(missing),
            )


def _split_csv(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def build_paci_authenticator_from_environ(
    environ: Optional[Mapping[str, str]] = None,
    *,
    jwks: Optional[JwksKeyProvider] = None,
    introspection: Optional[IntrospectionClient] = None,
    assertion_signer: Optional[ClientAssertionSigner] = None,
    now_fn: Optional[Callable[[], float]] = None,
) -> PaciJwtAuthenticator:
    """Factory for ``LINKSKILLS_PLATFORM_AUTHENTICATOR=...:build_paci_authenticator_from_environ``.

    Required env:
      - ``LINKSKILLS_PACI_ISSUER``
      - ``LINKSKILLS_PACI_JWKS_URI`` (same origin as issuer)
      - ``LINKSKILLS_PACI_AUDIENCE`` (comma-separated; default ``lskills-api``)

    Optional env:
      - ``LINKSKILLS_PACI_REQUIRED_SERVICE_SCOPES`` (default ``lskills``)
      - ``LINKSKILLS_PACI_INTROSPECTION_URL`` (required for high-risk writes)
      - ``LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID``
    """
    env = environ if environ is not None else os.environ
    issuer = str(env.get(ENV_PACI_ISSUER) or "").strip()
    jwks_uri = str(env.get(ENV_PACI_JWKS_URI) or "").strip()
    if not issuer or not jwks_uri:
        raise AuthConfigurationError(
            f"PACI authenticator requires {ENV_PACI_ISSUER} and {ENV_PACI_JWKS_URI}"
        )
    audiences = _split_csv(str(env.get(ENV_PACI_AUDIENCE) or DEFAULT_AUDIENCE))
    scopes = _split_csv(
        str(env.get(ENV_PACI_REQUIRED_SERVICE_SCOPES) or DEFAULT_SERVICE_SCOPE)
    )

    jwks_provider: JwksKeyProvider
    if jwks is not None:
        jwks_provider = jwks
    else:
        jwks_provider = CachedJwksClient(
            issuer=issuer,
            jwks_uri=jwks_uri,
            now_fn=now_fn,
        )

    introspect_client = introspection
    introspect_url = str(env.get(ENV_PACI_INTROSPECTION_URL) or "").strip()
    if introspect_client is None and introspect_url:
        client_id = str(env.get(ENV_PACI_INTROSPECTION_CLIENT_ID) or "").strip()
        if not client_id:
            raise AuthConfigurationError(
                f"{ENV_PACI_INTROSPECTION_URL} set but "
                f"{ENV_PACI_INTROSPECTION_CLIENT_ID} missing"
            )
        signer = assertion_signer or StubClientAssertionSigner()
        introspect_client = IntrospectionClient(
            introspection_url=introspect_url,
            client_id=client_id,
            assertion_signer=signer,
            now_fn=now_fn,
        )

    return PaciJwtAuthenticator(
        issuer=issuer,
        audiences=audiences,
        jwks=jwks_provider,
        introspection=introspect_client,
        required_service_scopes=scopes,
        now_fn=now_fn,
    )
