"""Platform AuthClaims verification for LiNKskills Gateway.

Consumes the frozen contract ``platform.auth-claims/1.1.0`` from
LiNKplatform (vendored schema bytes pin).

Authenticity rules (wave 4):
- Production ``PlatformClaimsVerifier`` never accepts unsigned
  ``platform.<base64url(JSON)>`` tokens. It requires an injected
  Platform-approved cryptographic authenticator (signature + issuer trust).
- Unsigned decoding lives only on ``LocalUnsignedClaimsVerifier`` and is
  permitted solely when ``LINKSKILLS_AUTH_MODE=local-test`` or an explicit
  local-test verifier is injected.
- Claim-field shape remains frozen camelCase AuthClaims (no renaming).

Wave 5: pin ``1.1.0`` (orgId null only when actorKind is service) and enforce
exact ``permittedOperations`` for Gateway/MCP reads and mutations.
"""

from __future__ import annotations

import base64
import hashlib
import importlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Protocol, Set


CLAIM_CONTRACT_VERSION = "platform.auth-claims/1.1.0"
PLATFORM_CONTRACTS_PACKAGE = "0.2.2"
AUTH_MODE_PRODUCTION = "production"
AUTH_MODE_LOCAL_TEST = "local-test"
ACTOR_KINDS = frozenset(
    {"human", "persona", "service", "adapter", "program_executor"}
)
ALLOWED_CLAIM_KEYS = frozenset(
    {
        "claimContractVersion",
        "actorId",
        "actorKind",
        "runtimeBindingId",
        "credentialId",
        "orgId",
        "internal",
        "serviceScopes",
        "permittedOperations",
        "issuedAt",
        "expiresAt",
        "issuer",
        "audience",
        "programRestrictions",
        "repositoryRestrictions",
        "correlationId",
    }
)
REQUIRED_CLAIM_KEYS = frozenset(
    {
        "claimContractVersion",
        "actorId",
        "actorKind",
        "runtimeBindingId",
        "credentialId",
        "orgId",
        "internal",
        "serviceScopes",
        "permittedOperations",
        "issuedAt",
        "expiresAt",
        "issuer",
        "audience",
        "correlationId",
    }
)

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "schemas"
    / "platform-auth-claims.v1.1.0.json"
)
CLAIM_FIXTURES_DIR = (
    Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "platform-claims"
)
EXPECTED_SCHEMA_BYTES_SHA256 = (
    "c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1"
)
EXPECTED_SCHEMA_CONTENT_HASH = (
    "fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567"
)

# High-risk mutating writes that require PACI RFC 7662 introspection when the
# PACI authenticator is configured (envelope §7.4 / §8 step 6). Matches Skills
# Gateway WRITE_OPERATIONS (durable mutations + external side effects).
# PACI envelope pin: platform.auth-token-envelope/0.1.0 /
# @linktrend/platform-contracts@0.3.0 / Platform HEAD
# 421a35e97bc302be0f5e1f196d0a5e8d132f6fd8 (AuthClaims claim-shape package remains
# 0.2.2 historically; PACI adoption uses 0.3.0 — see paci_types.py).
HIGH_RISK_WRITE_OPERATIONS: frozenset[str] = frozenset(
    {
        "skills_run_start",
        "skills_run_update",
        "skills_run_complete",
        "skills_run_fail",
        "skills_tool_invoke",
        "skills_feedback_submit",
        "skills_trace_candidate_submit",
    }
)

# Gateway operation -> accepted permittedOperations tokens (exact membership).
OPERATION_PERMISSIONS: Dict[str, frozenset[str]] = {
    "skills_list": frozenset({"read", "skills:read"}),
    "skills_search": frozenset({"read", "skills:read"}),
    "skills_describe": frozenset({"read", "skills:read"}),
    "skills_fragment_get": frozenset({"read", "skills:read"}),
    "skills_release_get": frozenset({"read", "skills:read"}),
    "skills_tool_resolve": frozenset({"read", "skills:read", "execute", "skills:write"}),
    "skills_input_validate": frozenset({"read", "skills:read", "execute", "skills:write"}),
    "skills_output_validate": frozenset({"read", "skills:read", "execute", "skills:write"}),
    "skills_run_start": frozenset({"execute", "skills:write", "skills:run"}),
    "skills_run_update": frozenset({"execute", "skills:write", "skills:run"}),
    "skills_run_complete": frozenset({"execute", "skills:write", "skills:run"}),
    "skills_run_fail": frozenset({"execute", "skills:write", "skills:run"}),
    "skills_tool_invoke": frozenset({"execute", "skills:write"}),
    "skills_feedback_submit": frozenset(
        {"skills:feedback", "execute", "skills:write", "skills:run"}
    ),
    "skills_trace_candidate_submit": frozenset(
        {"skills:feedback", "execute", "skills:write", "skills:run"}
    ),
}

_PROTECTED_IDENTITY_KEYS = frozenset(
    {
        "actorId",
        "actor_id",
        "platform_actor_id",
        "actorKind",
        "actor_kind",
        "orgId",
        "org_id",
        "credentialId",
        "credential_id",
        "runtimeBindingId",
        "serviceScopes",
        "scopes",
        "permittedOperations",
        "expiresAt",
        "exp",
    }
)


class AuthError(Exception):
    """Raised when claims are missing, expired, malformed, or spoofed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class AuthConfigurationError(Exception):
    """Raised when production auth cannot start fail-closed (missing verifier/keys)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class ActorClaims:
    """Verified platform actor claims consumed by LiNKskills Gateway."""

    actor_id: str
    actor_kind: str
    org_id: Optional[str]
    scopes: frozenset[str] = field(default_factory=frozenset)
    permitted_operations: frozenset[str] = field(default_factory=frozenset)
    exp: int = 0
    credential_id: str = ""
    runtime_binding_id: str = ""
    claim_contract_version: str = ""
    issuer: str = ""
    audience: frozenset[str] = field(default_factory=frozenset)
    internal: bool = False
    correlation_id: str = ""
    raw: Mapping[str, Any] = field(default_factory=dict)

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or "*" in self.scopes

    def permits(self, *candidates: str) -> bool:
        """True when any candidate is present in permittedOperations (or ``*``)."""
        if "*" in self.permitted_operations:
            return True
        return bool(self.permitted_operations.intersection(candidates))

    def may_perform(self, operation: str) -> bool:
        allowed = OPERATION_PERMISSIONS.get(operation)
        if allowed is None:
            return False
        if not self.permitted_operations:
            return False
        return self.permits(*allowed)

    def may_read(self) -> bool:
        return self.has_scope("lskills") and self.permits("read", "skills:read")

    def may_write(self) -> bool:
        return self.has_scope("lskills") and self.permits(
            "execute", "skills:write", "skills:run", "skills:feedback"
        )


@dataclass(frozen=True)
class AuthenticatedToken:
    """Cryptographically authenticated AuthClaims plus Platform trust context."""

    claims: Mapping[str, Any]
    credential_status: str = "active"
    actor_lifecycle_state: str = "active"
    binding_state: str = "active"


class PlatformTokenAuthenticator(Protocol):
    """Platform-approved cryptographic token authenticator.

    Implementations must verify signature (or equivalent Platform trust proof),
    issuer key material, and return the frozen AuthClaims payload. They must
    never accept unsigned ``platform.<base64url(JSON)>`` tokens.
    """

    def authenticate(self, token: str) -> AuthenticatedToken:
        """Verify authenticity and return AuthClaims + credential/binding status."""


def _canonicalize_json(value: Any) -> str:
    if value is None or isinstance(value, (str, int, float, bool)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_canonicalize_json(item) for item in value) + "]"
    if isinstance(value, dict):
        parts = [
            f"{json.dumps(key, ensure_ascii=False)}:{_canonicalize_json(value[key])}"
            for key in sorted(value)
        ]
        return "{" + ",".join(parts) + "}"
    raise TypeError(f"unsupported JSON type: {type(value)!r}")


def verify_frozen_auth_claims_schema() -> dict[str, str]:
    """Verify vendored schema matches frozen Platform contract hashes."""
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"missing frozen schema: {SCHEMA_PATH}")
    raw = SCHEMA_PATH.read_bytes()
    file_sha = hashlib.sha256(raw).hexdigest()
    if file_sha != EXPECTED_SCHEMA_BYTES_SHA256:
        raise AuthError(
            "auth_contract_mismatch",
            f"platform-auth-claims schema bytes SHA-256 mismatch: {file_sha}",
        )
    content_hash = hashlib.sha256(
        _canonicalize_json(json.loads(raw.decode("utf-8"))).encode("utf-8")
    ).hexdigest()
    if content_hash != EXPECTED_SCHEMA_CONTENT_HASH:
        raise AuthError(
            "auth_contract_mismatch",
            f"platform-auth-claims contentHash mismatch: {content_hash}",
        )
    return {
        "contract": CLAIM_CONTRACT_VERSION,
        "package": PLATFORM_CONTRACTS_PACKAGE,
        "schema_bytes_sha256": file_sha,
        "content_hash": content_hash,
    }


def _parse_iso8601_to_epoch(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return int(datetime.fromisoformat(text).timestamp())
    except ValueError as exc:
        raise AuthError("auth_invalid", f"expiresAt/issuedAt not ISO-8601: {value!r}") from exc


def resolve_auth_mode(environ: Optional[Mapping[str, str]] = None) -> str:
    """Return normalized auth mode (``production`` or ``local-test``)."""
    env = environ if environ is not None else os.environ
    raw = str(env.get("LINKSKILLS_AUTH_MODE") or AUTH_MODE_PRODUCTION).strip().lower()
    if raw in {"local-test", "test", "local_test"}:
        return AUTH_MODE_LOCAL_TEST
    if raw in {"production", "prod", ""}:
        return AUTH_MODE_PRODUCTION
    raise AuthConfigurationError(
        f"Unknown LINKSKILLS_AUTH_MODE={raw!r}; expected 'production' or 'local-test'"
    )


class _AuthClaimsPolicy:
    """Shared frozen AuthClaims shape + lifecycle policy (not authenticity)."""

    def __init__(
        self,
        *,
        now_fn: Optional[Callable[[], float]] = None,
        expected_audience: str = "lskills-api",
        required_service: str = "lskills",
        require_internal: Optional[bool] = None,
        expected_org_id: Optional[str] = None,
        expected_issuer: Optional[str] = "linkplatform-issuer",
    ) -> None:
        self._now = now_fn or time.time
        self.expected_audience = expected_audience
        self.required_service = required_service
        self.require_internal = require_internal
        self.expected_org_id = expected_org_id
        self.expected_issuer = expected_issuer

    def normalize_claims(self, raw: Mapping[str, Any]) -> ActorClaims:
        unknown = sorted(set(raw.keys()) - ALLOWED_CLAIM_KEYS)
        if unknown:
            raise AuthError(
                "auth_invalid",
                "unknown AuthClaims fields rejected: " + ", ".join(unknown),
            )
        missing = sorted(REQUIRED_CLAIM_KEYS - set(raw.keys()))
        if missing:
            raise AuthError(
                "auth_invalid",
                "missing required AuthClaims fields: " + ", ".join(missing),
            )

        claim_version = str(raw["claimContractVersion"]).strip()
        if claim_version != CLAIM_CONTRACT_VERSION:
            raise AuthError(
                "auth_contract_mismatch",
                f"claimContractVersion must be {CLAIM_CONTRACT_VERSION!r}, got {claim_version!r}",
            )

        actor_id = str(raw["actorId"]).strip()
        actor_kind = str(raw["actorKind"]).strip()
        if not actor_id:
            raise AuthError("auth_invalid", "actorId is required")
        if actor_kind not in ACTOR_KINDS:
            raise AuthError(
                "auth_invalid",
                f"actorKind must be one of {sorted(ACTOR_KINDS)}; got {actor_kind!r}",
            )

        org_raw = raw["orgId"]
        if org_raw is None:
            if actor_kind != "service":
                raise AuthError(
                    "auth_invalid",
                    "orgId may be null only when actorKind is service",
                )
            org_id: Optional[str] = None
        else:
            org_id = str(org_raw).strip()
            if not org_id:
                raise AuthError("auth_invalid", "orgId must be non-empty string or null")

        if not isinstance(raw["internal"], bool):
            raise AuthError("auth_invalid", "internal must be boolean")

        scopes = self._as_string_set(raw["serviceScopes"], field_name="serviceScopes")
        if not scopes:
            raise AuthError("auth_invalid", "serviceScopes must be non-empty")
        ops = self._as_string_set(
            raw["permittedOperations"], field_name="permittedOperations", allow_empty=True
        )
        audience = self._as_string_set(raw["audience"], field_name="audience")
        if not audience:
            raise AuthError("auth_invalid", "audience must be non-empty")

        credential_id = str(raw["credentialId"]).strip()
        runtime_binding_id = str(raw["runtimeBindingId"]).strip()
        issuer = str(raw["issuer"]).strip()
        correlation_id = str(raw["correlationId"]).strip()
        if not credential_id:
            raise AuthError("auth_invalid", "credentialId is required")
        if not runtime_binding_id:
            raise AuthError("auth_invalid", "runtimeBindingId is required")
        if not issuer:
            raise AuthError("auth_invalid", "issuer is required")
        if not correlation_id:
            raise AuthError("auth_invalid", "correlationId is required")

        exp = _parse_iso8601_to_epoch(raw["expiresAt"])
        _parse_iso8601_to_epoch(raw["issuedAt"])

        return ActorClaims(
            actor_id=actor_id,
            actor_kind=actor_kind,
            org_id=org_id,
            scopes=frozenset(scopes),
            permitted_operations=frozenset(ops),
            exp=exp,
            credential_id=credential_id,
            runtime_binding_id=runtime_binding_id,
            claim_contract_version=claim_version,
            issuer=issuer,
            audience=frozenset(audience),
            internal=bool(raw["internal"]),
            correlation_id=correlation_id,
            raw=dict(raw),
        )

    @staticmethod
    def _as_string_set(
        value: Any, *, field_name: str, allow_empty: bool = False
    ) -> Set[str]:
        if isinstance(value, str):
            raise AuthError("auth_invalid", f"{field_name} must be an array of strings")
        if not isinstance(value, list):
            raise AuthError("auth_invalid", f"{field_name} must be an array of strings")
        out = {str(item).strip() for item in value}
        if "" in out:
            raise AuthError("auth_invalid", f"{field_name} entries must be non-empty")
        if not out and not allow_empty:
            raise AuthError("auth_invalid", f"{field_name} must be non-empty")
        return out

    def _resolve_now(self, now: Optional[Any]) -> int:
        if now is None:
            return int(self._now())
        if isinstance(now, (int, float)):
            return int(now)
        return _parse_iso8601_to_epoch(now)

    def check_lifecycle(
        self,
        claims: ActorClaims,
        *,
        required_operation: Optional[str],
        now: Optional[Any],
        credential_status: str = "active",
        actor_lifecycle_state: str = "active",
        binding_state: str = "active",
    ) -> None:
        status = (credential_status or "active").strip().lower()
        if status in {"revoked", "rotated"}:
            raise AuthError("auth_revoked", f"Credential status rejected: {status}")
        if status == "expired":
            raise AuthError("auth_expired", "Credential status expired")
        if status != "active":
            raise AuthError(
                "auth_forbidden",
                f"Unsupported credential status: {status}",
            )

        if (actor_lifecycle_state or "active").strip().lower() != "active":
            raise AuthError(
                "auth_forbidden",
                f"Actor lifecycle not active: {actor_lifecycle_state}",
            )
        if (binding_state or "active").strip().lower() != "active":
            raise AuthError(
                "auth_forbidden",
                f"Runtime binding not active: {binding_state}",
            )

        now_epoch = self._resolve_now(now)
        if claims.exp <= now_epoch:
            raise AuthError("auth_expired", "Claims expired")

        issued_epoch = _parse_iso8601_to_epoch(claims.raw["issuedAt"])
        if now_epoch < issued_epoch:
            raise AuthError("auth_not_yet_valid", "Claims not yet valid")

        if self.expected_issuer is not None and claims.issuer != self.expected_issuer:
            raise AuthError(
                "auth_forbidden",
                f"Wrong issuer: expected {self.expected_issuer!r}, got {claims.issuer!r}",
            )

        if self.required_service not in claims.scopes and "*" not in claims.scopes:
            raise AuthError(
                "auth_forbidden",
                f"Missing required service scope: {self.required_service}",
            )
        if (
            self.expected_audience not in claims.audience
            and "*" not in claims.audience
        ):
            raise AuthError(
                "auth_forbidden",
                f"Missing required audience: {self.expected_audience}",
            )
        if self.require_internal is True and not claims.internal:
            raise AuthError("auth_forbidden", "Internal actor required")
        if self.expected_org_id is not None and claims.org_id != self.expected_org_id:
            raise AuthError("auth_forbidden", "wrong_org")
        if required_operation:
            # Accept either a permission token (skills:read) or a Gateway/MCP
            # operation name (skills_list) mapped via OPERATION_PERMISSIONS.
            if required_operation in OPERATION_PERMISSIONS:
                allowed = set(OPERATION_PERMISSIONS[required_operation])
            else:
                aliases = {
                    "skills:read": {"read", "skills:read"},
                    "skills:write": {"execute", "skills:write"},
                    "read": {"read", "skills:read"},
                    "execute": {"execute", "skills:write"},
                }
                allowed = aliases.get(required_operation, {required_operation})
            if (
                not (allowed & set(claims.permitted_operations))
                and "*" not in claims.permitted_operations
            ):
                raise AuthError(
                    "auth_forbidden",
                    f"Operation not permitted: {required_operation}",
                )

    def reject_override_headers(
        self,
        request_headers: Optional[Mapping[str, Any]],
    ) -> None:
        if not request_headers:
            return
        normalized = {str(k).lower(): v for k, v in request_headers.items()}
        forbidden = (
            "x-actor-id",
            "x-actor-kind",
            "x-org-id",
            "x-platform-actor-id",
            "x-credential-id",
            "x-actor-scopes",
            "x-scopes",
            "x-identity",
            "x-platform-claims",
        )
        present = [h for h in forbidden if h in normalized and normalized[h] not in (None, "")]
        if present:
            raise AuthError(
                "auth_spoof_rejected",
                "Client-supplied actor override headers are not accepted as authority: "
                + ", ".join(present),
            )

    def reject_spoof(
        self,
        claims: ActorClaims,
        request_payload: Optional[Mapping[str, Any]],
    ) -> None:
        if not request_payload:
            return
        candidates: list[Mapping[str, Any]] = [request_payload]
        for key in ("actor", "identity", "claims", "platform_claims", "actor_claims"):
            nested = request_payload.get(key)
            if isinstance(nested, Mapping):
                candidates.append(nested)

        expected = {
            "actorId": claims.actor_id,
            "actor_id": claims.actor_id,
            "platform_actor_id": claims.actor_id,
            "actorKind": claims.actor_kind,
            "actor_kind": claims.actor_kind,
            "orgId": claims.org_id,
            "org_id": claims.org_id,
            "credentialId": claims.credential_id,
            "credential_id": claims.credential_id,
        }
        for bag in candidates:
            for key in _PROTECTED_IDENTITY_KEYS:
                if key not in bag:
                    continue
                if key in {"serviceScopes", "scopes", "permittedOperations", "audience"}:
                    continue
                expected_value = expected.get(key)
                if expected_value is None and key in {"orgId", "org_id"}:
                    expected_value = claims.org_id
                if expected_value is None:
                    continue
                if str(provided := bag[key]) != str(expected_value):
                    raise AuthError(
                        "auth_spoof_rejected",
                        f"Spoofed identity rejected: {key} mismatch ({provided!r})",
                    )


def decode_unsigned_platform_token(token: str) -> Dict[str, Any]:
    """Decode unsigned ``platform.<base64url(JSON)>`` — local-test use only."""
    if not token.startswith("platform."):
        raise AuthError(
            "auth_unsupported",
            "Unsigned decoder accepts only platform.<base64url(AuthClaims JSON)>",
        )
    if token.startswith("platform.sig."):
        raise AuthError(
            "auth_unsupported",
            "Signed platform.sig.* tokens are not handled by the unsigned decoder",
        )
    encoded = token[len("platform.") :]
    pad = "=" * (-len(encoded) % 4)
    try:
        decoded = base64.urlsafe_b64decode(encoded + pad)
        data = json.loads(decoded.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthError("auth_malformed", "Malformed platform token") from exc
    if not isinstance(data, dict):
        raise AuthError("auth_malformed", "Platform token payload must be an object")
    return data


class LocalUnsignedClaimsVerifier(_AuthClaimsPolicy):
    """Local-test-only verifier for unsigned ``platform.<base64url(JSON)>`` tokens.

    Must never be the default production Gateway/MCP verifier.
    """

    local_test_only = True

    def verify(
        self,
        authorization: Optional[str],
        *,
        request_payload: Optional[Mapping[str, Any]] = None,
        request_headers: Optional[Mapping[str, Any]] = None,
        required_operation: Optional[str] = None,
        now: Optional[Any] = None,
        credential_status: str = "active",
        actor_lifecycle_state: str = "active",
        binding_state: str = "active",
    ) -> ActorClaims:
        if not authorization:
            raise AuthError("auth_missing", "Authorization required")

        token = authorization.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        if token.startswith("fake."):
            raise AuthError(
                "auth_unsupported",
                "fake.* claim tokens are not accepted",
            )

        if token.startswith("{"):
            try:
                raw = json.loads(token)
            except json.JSONDecodeError as exc:
                raise AuthError("auth_malformed", "Malformed JSON token") from exc
            if not isinstance(raw, dict):
                raise AuthError("auth_malformed", "JSON token must be an object")
        else:
            raw = decode_unsigned_platform_token(token)

        claims = self.normalize_claims(raw)
        self.check_lifecycle(
            claims,
            required_operation=required_operation,
            now=now,
            credential_status=credential_status,
            actor_lifecycle_state=actor_lifecycle_state,
            binding_state=binding_state,
        )
        self.reject_spoof(claims, request_payload)
        self.reject_override_headers(request_headers)
        return claims

    # Backward-compatible private aliases used by MCP spoof checks.
    def _reject_spoof(
        self,
        claims: ActorClaims,
        request_payload: Optional[Mapping[str, Any]],
    ) -> None:
        self.reject_spoof(claims, request_payload)


class PlatformClaimsVerifier(_AuthClaimsPolicy):
    """Production verifier: Platform-approved cryptographic authenticity required.

    Never decodes unsigned ``platform.<base64url(JSON)>`` tokens. Construction
    without a ``PlatformTokenAuthenticator`` is a configuration error.
    """

    local_test_only = False

    def __init__(
        self,
        authenticator: Optional[PlatformTokenAuthenticator] = None,
        *,
        now_fn: Optional[Callable[[], float]] = None,
        expected_audience: str = "lskills-api",
        required_service: str = "lskills",
        require_internal: Optional[bool] = None,
        expected_org_id: Optional[str] = None,
        expected_issuer: Optional[str] = "linkplatform-issuer",
        allow_missing_authenticator: bool = False,
    ) -> None:
        super().__init__(
            now_fn=now_fn,
            expected_audience=expected_audience,
            required_service=required_service,
            require_internal=require_internal,
            expected_org_id=expected_org_id,
            expected_issuer=expected_issuer,
        )
        if authenticator is None and not allow_missing_authenticator:
            raise AuthConfigurationError(
                "PlatformClaimsVerifier requires an injected Platform-approved "
                "cryptographic authenticator; unsigned platform.<base64url(JSON)> "
                "tokens are not accepted outside LINKSKILLS_AUTH_MODE=local-test"
            )
        self.authenticator = authenticator

    def verify(
        self,
        authorization: Optional[str],
        *,
        request_payload: Optional[Mapping[str, Any]] = None,
        request_headers: Optional[Mapping[str, Any]] = None,
        required_operation: Optional[str] = None,
        now: Optional[Any] = None,
        credential_status: Optional[str] = None,
        actor_lifecycle_state: Optional[str] = None,
        binding_state: Optional[str] = None,
    ) -> ActorClaims:
        if self.authenticator is None:
            raise AuthConfigurationError(
                "PlatformClaimsVerifier has no cryptographic authenticator configured"
            )
        if not authorization:
            raise AuthError("auth_missing", "Authorization required")

        token = authorization.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        if token.startswith("fake."):
            raise AuthError(
                "auth_unsupported",
                "fake.* claim tokens are not accepted on the production verifier",
            )

        # Explicitly refuse the unsigned local-test formats.
        if token.startswith("{") or (
            token.startswith("platform.") and not token.startswith("platform.sig.")
        ):
            raise AuthError(
                "auth_unsigned_rejected",
                "Unsigned platform.<base64url(JSON)> / raw JSON bearers are not "
                "accepted outside local-test mode",
            )

        # Prefer operation-aware auth when the authenticator supports PACI
        # high-risk introspection (envelope §8 step 6). Non-PACI authenticators
        # keep authenticate(token) only.
        authenticate_for_operation = getattr(
            self.authenticator, "authenticate_for_operation", None
        )
        if callable(authenticate_for_operation):
            authenticated = authenticate_for_operation(
                token, operation=required_operation
            )
        else:
            authenticated = self.authenticator.authenticate(token)
        claims = self.normalize_claims(authenticated.claims)
        self.check_lifecycle(
            claims,
            required_operation=required_operation,
            now=now,
            credential_status=credential_status or authenticated.credential_status,
            actor_lifecycle_state=actor_lifecycle_state
            or authenticated.actor_lifecycle_state,
            binding_state=binding_state or authenticated.binding_state,
        )
        self.reject_spoof(claims, request_payload)
        self.reject_override_headers(request_headers)
        return claims

    def _reject_spoof(
        self,
        claims: ActorClaims,
        request_payload: Optional[Mapping[str, Any]],
    ) -> None:
        self.reject_spoof(claims, request_payload)


def load_platform_authenticator_from_environ(
    environ: Optional[Mapping[str, str]] = None,
) -> PlatformTokenAuthenticator:
    """Load a Platform-approved authenticator from env; fail closed if absent.

    Expected: ``LINKSKILLS_PLATFORM_AUTHENTICATOR=package.module:factory_or_class``
    The object must be a ``PlatformTokenAuthenticator`` instance or a zero-arg
    callable returning one. LiNKskills does not ship Platform signing keys.
    """
    env = environ if environ is not None else os.environ
    ref = str(env.get("LINKSKILLS_PLATFORM_AUTHENTICATOR") or "").strip()
    if not ref:
        raise AuthConfigurationError(
            "Production auth requires LINKSKILLS_PLATFORM_AUTHENTICATOR="
            "module.path:attr (Platform-approved cryptographic verifier). "
            "Unsigned decoding is disabled outside LINKSKILLS_AUTH_MODE=local-test."
        )
    if ":" not in ref:
        raise AuthConfigurationError(
            "LINKSKILLS_PLATFORM_AUTHENTICATOR must be 'module.path:attr'"
        )
    module_name, attr_name = ref.split(":", 1)
    try:
        module = importlib.import_module(module_name)
        target = getattr(module, attr_name)
    except Exception as exc:  # noqa: BLE001 — configuration boundary
        raise AuthConfigurationError(
            f"Failed to load Platform authenticator {ref!r}: {exc}"
        ) from exc
    authenticator = target() if callable(target) and not hasattr(target, "authenticate") else target
    if not hasattr(authenticator, "authenticate"):
        raise AuthConfigurationError(
            f"Authenticator {ref!r} does not provide authenticate()"
        )
    return authenticator  # type: ignore[no-any-return]


def resolve_claims_verifier(
    *,
    verifier: Optional[Any] = None,
    authenticator: Optional[PlatformTokenAuthenticator] = None,
    environ: Optional[Mapping[str, str]] = None,
    allow_local_test: bool = True,
    **policy_kwargs: Any,
) -> Any:
    """Resolve the Gateway/MCP claims verifier fail-closed.

    - Explicit ``verifier`` wins (caller-injected).
    - ``LINKSKILLS_AUTH_MODE=local-test`` → ``LocalUnsignedClaimsVerifier``
      (unless ``allow_local_test=False``, e.g. canary).
    - Otherwise production cryptographic verifier; missing authenticator/config
      raises ``AuthConfigurationError`` (never falls back to unsigned).
    - When ``expected_issuer`` is omitted, prefer the authenticator's pinned
      ``issuer`` (PACI) or ``LINKSKILLS_PACI_ISSUER``; otherwise retain the
      ``PlatformClaimsVerifier`` default ``linkplatform-issuer``.
    """
    if verifier is not None:
        return verifier

    mode = resolve_auth_mode(environ)
    if mode == AUTH_MODE_LOCAL_TEST:
        if not allow_local_test:
            raise AuthConfigurationError(
                "local-test unsigned auth is not permitted in this context"
            )
        return LocalUnsignedClaimsVerifier(**policy_kwargs)

    auth = authenticator or load_platform_authenticator_from_environ(environ)
    # PACI authenticators pin issuer from LINKSKILLS_PACI_ISSUER during JWT
    # verify. Align the outer AuthClaims policy with that pin so a live PACI
    # issuer (e.g. Mac Mini canary URL) is not denied after crypto success by
    # the legacy default expected_issuer='linkplatform-issuer'. Non-PACI
    # authenticators without a pinned issuer keep the default. Explicit
    # expected_issuer in policy_kwargs always wins (including None to skip
    # the duplicate policy check when the caller opts in).
    if "expected_issuer" not in policy_kwargs:
        pinned = getattr(auth, "issuer", None)
        if isinstance(pinned, str) and pinned.strip():
            policy_kwargs["expected_issuer"] = pinned.strip()
        else:
            env = environ if environ is not None else os.environ
            paci_issuer = str(env.get("LINKSKILLS_PACI_ISSUER") or "").strip()
            if paci_issuer:
                policy_kwargs["expected_issuer"] = paci_issuer
    return PlatformClaimsVerifier(authenticator=auth, **policy_kwargs)


def load_platform_claim_fixture(name: str) -> Dict[str, Any]:
    """Load a vendored Platform claims fixture by file stem."""
    path = CLAIM_FIXTURES_DIR / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"platform claim fixture not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"fixture must be an object: {path}")
    return data
