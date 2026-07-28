"""Platform AuthClaims verification for LiNKskills Gateway.

Consumes the frozen contract ``platform.auth-claims/1.0.0`` from
``@linktrend/platform-contracts@0.2.1``.

Production verifier rules:
- exact ``claimContractVersion == "platform.auth-claims/1.0.0"``
- camelCase fields only; unknown keys rejected
- no snake_case aliases, no ``fake.*`` tokens, no actorKind ``agent``
- actorKind enum: human | persona | service | adapter | program_executor
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Set


CLAIM_CONTRACT_VERSION = "platform.auth-claims/1.0.0"
PLATFORM_CONTRACTS_PACKAGE = "0.2.1"
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
    / "platform-auth-claims.v1.0.0.json"
)
CLAIM_FIXTURES_DIR = (
    Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "platform-claims"
)
EXPECTED_SCHEMA_BYTES_SHA256 = (
    "b0397cdf34e76ab0986c6d223ecb6c3c66d619ea59557f78cd45c0c015ff50fb"
)
EXPECTED_SCHEMA_CONTENT_HASH = (
    "6bf49618d846662976886f57d5d468f73a08ab1a6574968f68833d82429db251"
)

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


class PlatformClaimsVerifier:
    """Verify frozen ``platform.auth-claims/1.0.0`` AuthClaims."""

    def __init__(
        self,
        *,
        now_fn: Optional[Callable[[], float]] = None,
        expected_audience: str = "lskills-api",
        required_service: str = "lskills",
        require_internal: Optional[bool] = None,
        expected_org_id: Optional[str] = None,
    ) -> None:
        self._now = now_fn or time.time
        self.expected_audience = expected_audience
        self.required_service = required_service
        self.require_internal = require_internal
        self.expected_org_id = expected_org_id

    def verify(
        self,
        authorization: Optional[str],
        *,
        request_payload: Optional[Mapping[str, Any]] = None,
        request_headers: Optional[Mapping[str, Any]] = None,
        required_operation: Optional[str] = None,
        now: Optional[Any] = None,
    ) -> ActorClaims:
        if not authorization:
            raise AuthError("auth_missing", "Authorization required")

        token = authorization.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        if token.startswith("fake."):
            raise AuthError(
                "auth_unsupported",
                "fake.* claim tokens are not accepted; use platform.<base64url(AuthClaims)>",
            )

        raw = self._decode_token(token)
        claims = self._normalize_claims(raw)
        self._check_lifecycle(claims, required_operation=required_operation, now=now)
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

    def _check_lifecycle(
        self,
        claims: ActorClaims,
        *,
        required_operation: Optional[str],
        now: Optional[Any],
    ) -> None:
        now_epoch = self._resolve_now(now)
        if claims.exp <= now_epoch:
            raise AuthError("auth_expired", "Claims expired")

        issued_epoch = _parse_iso8601_to_epoch(claims.raw["issuedAt"])
        if now_epoch < issued_epoch:
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
        if self.expected_org_id is not None and claims.org_id != self.expected_org_id:
            raise AuthError("auth_forbidden", "wrong_org")
        if required_operation and required_operation not in claims.permitted_operations:
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


def mint_platform_token(claims: Mapping[str, Any]) -> str:
    """Mint a ``platform.<b64>`` bearer token from canonical AuthClaims JSON."""
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
