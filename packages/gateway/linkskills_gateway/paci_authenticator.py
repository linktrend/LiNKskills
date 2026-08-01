"""PACI JWT ``PlatformTokenAuthenticator`` for LiNKskills Gateway.

Wire via::

    LINKSKILLS_PLATFORM_AUTHENTICATOR=\\
      linkskills_gateway.paci_authenticator:build_paci_authenticator_from_environ

**Evidence class:** local/fake conformance against frozen
``platform.auth-token-envelope/0.1.0``; not live-proven against Platform PACI.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Mapping, Optional, Sequence

from .auth import (
    AUTH_MODE_LOCAL_TEST,
    AuthConfigurationError,
    AuthError,
    AuthenticatedToken,
    HIGH_RISK_WRITE_OPERATIONS,
    resolve_auth_mode,
)
from .introspection import (
    ClientAssertionSigner,
    IntrospectionClient,
    LocalTestClientAssertionSigner,
    SecretRefClientAssertionSigner,
)
from .jwks import (
    CachedJwksClient,
    JwksKeyProvider,
    assert_https_transport,
    validate_issuer_identifier,
)
from .paci_jwt import PaciJwtVerifier
from .paci_types import (
    ENV_AUTH_MODE,
    EVIDENCE_STATUS_NOT_PROVEN,
    LOCAL_TEST_ASSERTION_SIGNER_GATE,
    PACI_ENVELOPE_CONTRACT,
    PLATFORM_CONTRACTS_PACKAGE_PACI,
)


# Environment variable names (documented for operators / canary fragments).
ENV_PACI_ISSUER = "LINKSKILLS_PACI_ISSUER"
ENV_PACI_JWKS_URI = "LINKSKILLS_PACI_JWKS_URI"
ENV_PACI_AUDIENCE = "LINKSKILLS_PACI_AUDIENCE"
ENV_PACI_REQUIRED_SERVICE_SCOPES = "LINKSKILLS_PACI_REQUIRED_SERVICE_SCOPES"
ENV_PACI_INTROSPECTION_URL = "LINKSKILLS_PACI_INTROSPECTION_URL"
# Resource-server private_key_jwt assertion identity (who calls introspect).
ENV_PACI_INTROSPECTION_CLIENT_ID = "LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID"
# CSV allow-list of access-token mint client IDs permitted in active responses.
ENV_PACI_TRUSTED_MINT_CLIENT_IDS = "LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS"
ENV_PLATFORM_AUTHENTICATOR = "LINKSKILLS_PLATFORM_AUTHENTICATOR"

DEFAULT_AUDIENCE = "lskills-api"
DEFAULT_SERVICE_SCOPE = "lskills"


class PaciJwtAuthenticator:
    """PlatformTokenAuthenticator backed by PACI ES256 + optional introspection.

    ``authenticate(token)`` performs JWT/JWKS/AuthClaims verification.
    High-risk mutating writes must call ``authenticate_for_operation`` (or
    ``require_introspection``) so RFC 7662 active checks run fail-closed.

    Marked: local/fake frozen-envelope conformance; not live-proven.
    """

    evidence_status = EVIDENCE_STATUS_NOT_PROVEN
    envelope_contract = PACI_ENVELOPE_CONTRACT
    platform_contracts_package = PLATFORM_CONTRACTS_PACKAGE_PACI

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
        introspection_client_id: Optional[str] = None,
        trusted_mint_client_ids: Optional[Sequence[str]] = None,
        auth_mode: str = "production",
    ) -> None:
        validate_issuer_identifier(issuer, auth_mode=auth_mode)
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
        # RS assertion identity (who calls introspect) — not mint binding.
        self._introspection_client_id = str(introspection_client_id or "").strip()
        self._trusted_mint_client_ids = frozenset(
            str(c).strip() for c in (trusted_mint_client_ids or ()) if str(c).strip()
        )
        self._auth_mode = auth_mode

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
                expected_iss=verified.iss,
                expected_aud=sorted(verified.aud),
                expected_sub=verified.sub,
                expected_credential_id=str(verified.claims.get("credentialId") or ""),
                expected_runtime_binding_id=str(
                    verified.claims.get("runtimeBindingId") or ""
                ),
                expected_iat=verified.iat,
                expected_exp=verified.exp,
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
        expected_iss: str,
        expected_aud: Sequence[str],
        expected_sub: str,
        expected_credential_id: str,
        expected_runtime_binding_id: str,
        expected_iat: int,
        expected_exp: int,
    ) -> None:
        """Fail-closed introspection gate for high-risk writes."""
        if self._introspection is None:
            raise AuthError(
                "introspection_unavailable",
                "High-risk write requires PACI introspection but no client configured "
                f"({ENV_PACI_INTROSPECTION_URL})",
            )
        if not self._introspection_client_id:
            raise AuthError(
                "auth_config",
                "Introspection assertion client_id required "
                f"({ENV_PACI_INTROSPECTION_CLIENT_ID})",
            )
        if not self._trusted_mint_client_ids:
            raise AuthError(
                "auth_config",
                "Trusted mint client_id allow-list required "
                f"({ENV_PACI_TRUSTED_MINT_CLIENT_IDS}); fail-closed on ambiguity",
            )
        if not expected_credential_id:
            raise AuthError(
                "auth_invalid",
                "AuthClaims credentialId required for introspection binding",
            )
        if not expected_runtime_binding_id:
            raise AuthError(
                "auth_invalid",
                "AuthClaims runtimeBindingId required for introspection binding",
            )
        self._introspection.require_active(
            token,
            jti=jti,
            expected_iss=expected_iss,
            expected_aud=expected_aud,
            expected_sub=expected_sub,
            trusted_mint_client_ids=sorted(self._trusted_mint_client_ids),
            expected_credential_id=expected_credential_id,
            expected_runtime_binding_id=expected_runtime_binding_id,
            expected_iat=expected_iat,
            expected_exp=expected_exp,
            required_scopes=sorted(self.required_service_scopes),
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
      - ``LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID`` (RS assertion client id)
      - ``LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS`` (CSV mint client allow-list;
        required outside local-test when introspection is configured)
      - ``LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE`` (required outside local-test
        when introspection is configured)

    Outside ``LINKSKILLS_AUTH_MODE=local-test``, a real SecretRef-backed
    ``private_key_jwt`` signer is mandatory whenever introspection is enabled.
    ``LocalTestClientAssertionSigner`` is forbidden on production/stage paths.
    Missing ``LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS`` outside local-test also
    fails closed when introspection is configured.
    """
    env = environ if environ is not None else os.environ
    try:
        auth_mode = resolve_auth_mode(env)
    except Exception:  # noqa: BLE001
        # Fall back to explicit env read if auth resolver raises unexpectedly.
        raw = str(env.get(ENV_AUTH_MODE) or "production").strip().lower()
        auth_mode = raw if raw in {AUTH_MODE_LOCAL_TEST, "production"} else "production"

    issuer = str(env.get(ENV_PACI_ISSUER) or "").strip()
    jwks_uri = str(env.get(ENV_PACI_JWKS_URI) or "").strip()
    if not issuer or not jwks_uri:
        raise AuthConfigurationError(
            f"PACI authenticator requires {ENV_PACI_ISSUER} and {ENV_PACI_JWKS_URI}"
        )
    validate_issuer_identifier(issuer, auth_mode=auth_mode)
    assert_https_transport(jwks_uri, label="PACI jwks_uri", auth_mode=auth_mode)

    audiences = _split_csv(str(env.get(ENV_PACI_AUDIENCE) or DEFAULT_AUDIENCE))
    scopes = _split_csv(
        str(env.get(ENV_PACI_REQUIRED_SERVICE_SCOPES) or DEFAULT_SERVICE_SCOPE)
    )
    trusted_mint_ids = _split_csv(
        str(env.get(ENV_PACI_TRUSTED_MINT_CLIENT_IDS) or "")
    )

    jwks_provider: JwksKeyProvider
    if jwks is not None:
        jwks_provider = jwks
    else:
        jwks_provider = CachedJwksClient(
            issuer=issuer,
            jwks_uri=jwks_uri,
            now_fn=now_fn,
            auth_mode=auth_mode,
        )

    introspect_client = introspection
    introspect_url = str(env.get(ENV_PACI_INTROSPECTION_URL) or "").strip()
    # RS private_key_jwt assertion client id (who calls introspect).
    assertion_client_id = str(env.get(ENV_PACI_INTROSPECTION_CLIENT_ID) or "").strip()
    if introspect_client is None and introspect_url:
        if not assertion_client_id:
            raise AuthConfigurationError(
                f"{ENV_PACI_INTROSPECTION_URL} set but "
                f"{ENV_PACI_INTROSPECTION_CLIENT_ID} missing"
            )
        if auth_mode != AUTH_MODE_LOCAL_TEST and not trusted_mint_ids:
            raise AuthConfigurationError(
                f"{ENV_PACI_INTROSPECTION_URL} set but "
                f"{ENV_PACI_TRUSTED_MINT_CLIENT_IDS} missing or empty "
                "(fail-closed outside local-test)"
            )
        signer = assertion_signer
        if signer is None:
            if auth_mode == AUTH_MODE_LOCAL_TEST:
                # Explicit local-test gate only — never default stub in production.
                signer = LocalTestClientAssertionSigner(auth_mode=auth_mode)
            else:
                try:
                    signer = SecretRefClientAssertionSigner.from_environ(
                        env, now_fn=now_fn
                    )
                except AuthError as exc:
                    raise AuthConfigurationError(str(exc.message)) from exc
        elif isinstance(signer, LocalTestClientAssertionSigner):
            if auth_mode != AUTH_MODE_LOCAL_TEST:
                raise AuthConfigurationError(
                    "LocalTestClientAssertionSigner forbidden outside "
                    f"{LOCAL_TEST_ASSERTION_SIGNER_GATE}"
                )
        introspect_client = IntrospectionClient(
            introspection_url=introspect_url,
            client_id=assertion_client_id,
            assertion_signer=signer,
            now_fn=now_fn,
            auth_mode=auth_mode,
            required_scopes=scopes,
        )
    elif (
        introspect_client is not None
        and auth_mode != AUTH_MODE_LOCAL_TEST
        and not trusted_mint_ids
    ):
        # Injected introspection client still needs mint allow-list outside local-test.
        raise AuthConfigurationError(
            f"{ENV_PACI_TRUSTED_MINT_CLIENT_IDS} missing or empty "
            "(fail-closed outside local-test when introspection is configured)"
        )

    return PaciJwtAuthenticator(
        issuer=issuer,
        audiences=audiences,
        jwks=jwks_provider,
        introspection=introspect_client,
        required_service_scopes=scopes,
        now_fn=now_fn,
        introspection_client_id=assertion_client_id or None,
        trusted_mint_client_ids=trusted_mint_ids or None,
        auth_mode=auth_mode,
    )
