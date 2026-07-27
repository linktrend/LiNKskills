"""Platform actor claim verification for LiNKskills Gateway.

Consumes the canonical LiNKplatform AuthClaims shape
(`packages/contracts/src/claims.ts` / fixtures under
`packages/contracts/fixtures/claims/`).

Non-test Gateway paths use :class:`PlatformClaimsVerifier` only.
The legacy ``fake.<b64>`` snake_case shape is confined to
:mod:`linkskills_gateway.auth_testing` for unit tests.
"""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Set, Union


class AuthError(Exception):
    """Raised when claims are missing, expired, malformed, or spoofed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ActorClaims:
    """Verified platform actor claims consumed by LiNKskills Gateway."""

    actor_id: str
    actor_kind: str
    org_id: str
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

    def may_read(self) -> bool:
        return (
            self.has_scope("lskills")
            or "read" in self.permitted_operations
            or "skills:read" in self.permitted_operations
            or "*" in self.permitted_operations
        )

    def may_write(self) -> bool:
        return (
            self.has_scope("lskills")
            and (
                "execute" in self.permitted_operations
                or "skills:write" in self.permitted_operations
                or "*" in self.permitted_operations
            )
        ) or ("skills:write" in self.permitted_operations)


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

CLAIM_FIXTURES_DIR = (
    Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "platform-claims"
)


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


class PlatformClaimsVerifier:
    """Verify canonical Platform AuthClaims for Gateway requests.

    Accepted token formats:
    - ``platform.<base64url(json AuthClaims)>``
    - raw JSON object string (AuthClaims camelCase)
    - already-decoded mapping
    """

    def __init__(
        self,
        *,
        now_fn=None,
        expected_audience: str = "lskills-api",
        required_service: str = "lskills",
        require_internal: Optional[bool] = None,
    ) -> None:
        self._now = now_fn or time.time
        self.expected_audience = expected_audience
        self.required_service = required_service
        self.require_internal = require_internal

    def verify(
        self,
        authorization: Optional[str],
        *,
        request_payload: Optional[Mapping[str, Any]] = None,
        request_headers: Optional[Mapping[str, Any]] = None,
        required_operation: Optional[str] = None,
    ) -> ActorClaims:
        if not authorization:
            raise AuthError("auth_missing", "Authorization required")

        token = authorization.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        # Refuse the retired competing fake shape on the production verifier path.
        if token.startswith("fake."):
            raise AuthError(
                "auth_unsupported",
                "Competing fake.* claim tokens are not accepted on PlatformClaimsVerifier; "
                "use platform.<base64url(AuthClaims)> or test helpers in auth_testing",
            )

        raw = self._decode_token(token)
        claims = self._normalize_claims(raw)
        self._check_lifecycle(claims, required_operation=required_operation)
        self._reject_spoof(claims, request_payload)
        self._reject_override_headers(request_headers)
        return claims

    def _decode_token(self, token: str) -> Dict[str, Any]:
        if token.startswith("platform."):
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

        if token.startswith("{"):
            try:
                data = json.loads(token)
            except json.JSONDecodeError as exc:
                raise AuthError("auth_malformed", "Malformed JSON token") from exc
            if not isinstance(data, dict):
                raise AuthError("auth_malformed", "JSON token must be an object")
            return data

        raise AuthError(
            "auth_unsupported",
            "Unsupported token format; use platform.<base64url(AuthClaims JSON)>",
        )

    def _normalize_claims(self, raw: Mapping[str, Any]) -> ActorClaims:
        # Canonical camelCase fields from Platform AuthClaims.
        actor_id = str(
            raw.get("actorId") or raw.get("platform_actor_id") or raw.get("actor_id") or ""
        ).strip()
        actor_kind = str(raw.get("actorKind") or raw.get("actor_kind") or "").strip()
        org_id = str(raw.get("orgId") or raw.get("org_id") or "").strip()
        credential_id = str(raw.get("credentialId") or raw.get("credential_id") or "").strip()
        runtime_binding_id = str(
            raw.get("runtimeBindingId") or raw.get("runtime_binding_id") or ""
        ).strip()
        claim_version = str(
            raw.get("claimContractVersion") or raw.get("claim_schema_version") or ""
        ).strip()
        issuer = str(raw.get("issuer") or "").strip()
        correlation_id = str(raw.get("correlationId") or raw.get("correlation_id") or "").strip()
        internal = bool(raw.get("internal")) if "internal" in raw else bool(raw.get("internal_status"))

        scopes_raw = raw.get("serviceScopes") or raw.get("scopes") or []
        ops_raw = raw.get("permittedOperations") or []
        audience_raw = raw.get("audience") or []

        expires_at = raw.get("expiresAt") or raw.get("exp")
        if not actor_id:
            raise AuthError("auth_invalid", "actorId is required")
        if not actor_kind:
            raise AuthError("auth_invalid", "actorKind is required")
        if not claim_version:
            raise AuthError("auth_invalid", "claimContractVersion is required")
        if not credential_id:
            raise AuthError("auth_invalid", "credentialId is required")
        if expires_at is None:
            raise AuthError("auth_invalid", "expiresAt is required")
        if not issuer:
            raise AuthError("auth_invalid", "issuer is required")

        exp = _parse_iso8601_to_epoch(expires_at)

        def _as_set(value: Any, *, field_name: str) -> Set[str]:
            if isinstance(value, str):
                return {value}
            if isinstance(value, Iterable):
                return {str(s) for s in value}
            raise AuthError("auth_invalid", f"{field_name} must be a list of strings")

        scopes = _as_set(scopes_raw, field_name="serviceScopes")
        ops = _as_set(ops_raw, field_name="permittedOperations")
        audience = _as_set(audience_raw, field_name="audience")

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
            internal=internal,
            correlation_id=correlation_id,
            raw=dict(raw),
        )

    def _check_lifecycle(
        self,
        claims: ActorClaims,
        *,
        required_operation: Optional[str],
    ) -> None:
        now = int(self._now())
        if claims.exp <= now:
            raise AuthError("auth_expired", "Claims expired")

        issued_at = claims.raw.get("issuedAt")
        if issued_at is not None:
            try:
                issued_epoch = _parse_iso8601_to_epoch(issued_at)
            except AuthError:
                raise
            if now < issued_epoch:
                raise AuthError("auth_not_yet_valid", "Claims not yet valid")

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
        if required_operation and required_operation not in claims.permitted_operations:
            # Allow coarse read/execute aliases.
            aliases = {
                "skills:read": {"read", "skills:read"},
                "skills:write": {"execute", "skills:write"},
            }
            allowed = aliases.get(required_operation, {required_operation})
            if not (allowed & set(claims.permitted_operations)) and "*" not in claims.permitted_operations:
                raise AuthError(
                    "auth_forbidden",
                    f"Operation not permitted: {required_operation}",
                )

    def _reject_override_headers(
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

    def _reject_spoof(
        self,
        claims: ActorClaims,
        request_payload: Optional[Mapping[str, Any]],
    ) -> None:
        if not request_payload:
            return
        candidates: list[Mapping[str, Any]] = [request_payload]
        for key in ("actor", "identity", "claims", "platform_claims"):
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
                provided = bag[key]
                if key in {"serviceScopes", "scopes", "permittedOperations", "audience"}:
                    continue
                expected_value = expected.get(key)
                if expected_value is None:
                    continue
                if str(provided) != str(expected_value):
                    raise AuthError(
                        "auth_spoof_rejected",
                        f"Spoofed identity rejected: {key} mismatch",
                    )


def mint_platform_token(claims: Mapping[str, Any]) -> str:
    """Helper: mint a ``platform.<b64>`` bearer token from AuthClaims JSON."""
    payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return f"platform.{encoded}"


def load_platform_claim_fixture(name: str) -> Dict[str, Any]:
    """Load a vendored Platform claims fixture by file stem."""
    path = CLAIM_FIXTURES_DIR / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"platform claim fixture not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"fixture must be an object: {path}")
    return data


# Backward-compatible name used by older imports in tests — points at Platform verifier.