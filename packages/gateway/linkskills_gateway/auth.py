"""Platform actor claim verification (fake/conformance until live Platform).

LiNKplatform remains the canonical identity issuer. This module accepts the
shared claim shape for local/fake tests and rejects any attempt by a caller to
spoof identity fields that must be server-derived from verified claims.
"""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Set


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
    exp: int = 0
    credential_id: str = ""

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or "*" in self.scopes


# Identity fields that must never be accepted from an untrusted request body
# when they conflict with verified claims.
_PROTECTED_IDENTITY_KEYS = frozenset(
    {
        "actor_id",
        "actor_kind",
        "org_id",
        "scopes",
        "exp",
        "credential_id",
        "platform_actor_id",
    }
)


class FakePlatformClaimsVerifier:
    """Verify fake platform tokens / claim dicts for Gateway conformance.

    Token formats accepted:
    - ``fake.<base64url(json claims)>``
    - raw JSON object string (test convenience)
    - already-decoded mapping (in-process callers)

    Spoof rejection: if a request payload supplies protected identity keys that
    differ from the verified claims, verification fails closed.
    """

    def __init__(
        self,
        *,
        now_fn=None,
        required_scopes: Optional[Sequence[str]] = None,
        require_any_scope: bool = True,
    ) -> None:
        self._now = now_fn or time.time
        # Default: accept tokens that carry skills:read OR skills:write.
        self._required_scopes = tuple(
            required_scopes if required_scopes is not None else ("skills:read", "skills:write")
        )
        self._require_any_scope = require_any_scope

    def verify(
        self,
        authorization: Optional[str],
        *,
        request_payload: Optional[Mapping[str, Any]] = None,
        request_headers: Optional[Mapping[str, Any]] = None,
    ) -> ActorClaims:
        if not authorization:
            raise AuthError("auth_missing", "Authorization required")

        token = authorization.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        raw = self._decode_token(token)
        claims = self._normalize_claims(raw)
        self._check_expiry(claims)
        self._check_scopes(claims)
        self._reject_spoof(claims, request_payload)
        self._reject_override_headers(request_headers)
        return claims

    def _reject_override_headers(
        self,
        request_headers: Optional[Mapping[str, Any]],
    ) -> None:
        """Never treat client-supplied actor override headers as authority."""
        if not request_headers:
            return
        # Normalize header names to lowercase for comparison.
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

    def _decode_token(self, token: str) -> Dict[str, Any]:
        if token.startswith("fake."):
            encoded = token[len("fake.") :]
            pad = "=" * (-len(encoded) % 4)
            try:
                decoded = base64.urlsafe_b64decode(encoded + pad)
                data = json.loads(decoded.decode("utf-8"))
            except (ValueError, json.JSONDecodeError) as exc:
                raise AuthError("auth_malformed", "Malformed fake token") from exc
            if not isinstance(data, dict):
                raise AuthError("auth_malformed", "Fake token payload must be an object")
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
            "Unsupported token format; use fake.<base64url(json)> for FakePlatformClaimsVerifier",
        )

    def _normalize_claims(self, raw: Mapping[str, Any]) -> ActorClaims:
        actor_id = str(raw.get("actor_id") or raw.get("platform_actor_id") or "").strip()
        actor_kind = str(raw.get("actor_kind") or "").strip()
        org_id = str(raw.get("org_id") or "").strip()
        exp_raw = raw.get("exp")
        scopes_raw = raw.get("scopes") or []

        if not actor_id:
            raise AuthError("auth_invalid", "actor_id is required")
        if not actor_kind:
            raise AuthError("auth_invalid", "actor_kind is required")
        if not org_id:
            raise AuthError("auth_invalid", "org_id is required")
        if exp_raw is None:
            raise AuthError("auth_invalid", "exp is required")

        try:
            exp = int(exp_raw)
        except (TypeError, ValueError) as exc:
            raise AuthError("auth_invalid", "exp must be an integer unix timestamp") from exc

        if isinstance(scopes_raw, str):
            scopes: Set[str] = {scopes_raw}
        elif isinstance(scopes_raw, Iterable):
            scopes = {str(s) for s in scopes_raw}
        else:
            raise AuthError("auth_invalid", "scopes must be a list of strings")

        return ActorClaims(
            actor_id=actor_id,
            actor_kind=actor_kind,
            org_id=org_id,
            scopes=frozenset(scopes),
            exp=exp,
            credential_id=str(raw.get("credential_id") or ""),
        )

    def _check_expiry(self, claims: ActorClaims) -> None:
        now = int(self._now())
        if claims.exp <= now:
            raise AuthError("auth_expired", "Claims expired")

    def _check_scopes(self, claims: ActorClaims) -> None:
        if "*" in claims.scopes:
            return
        if not self._required_scopes:
            return
        if self._require_any_scope:
            if any(scope in claims.scopes for scope in self._required_scopes):
                return
            raise AuthError(
                "auth_forbidden",
                "Missing required scopes: need one of "
                + ", ".join(self._required_scopes),
            )
        missing = [s for s in self._required_scopes if s not in claims.scopes]
        if missing:
            raise AuthError(
                "auth_forbidden",
                f"Missing required scopes: {', '.join(missing)}",
            )

    def _reject_spoof(
        self,
        claims: ActorClaims,
        request_payload: Optional[Mapping[str, Any]],
    ) -> None:
        if not request_payload:
            return

        # Nested identity bags (common spoof vector).
        candidates: list[Mapping[str, Any]] = [request_payload]
        for key in ("actor", "identity", "claims", "platform_claims"):
            nested = request_payload.get(key)
            if isinstance(nested, Mapping):
                candidates.append(nested)

        expected = {
            "actor_id": claims.actor_id,
            "platform_actor_id": claims.actor_id,
            "actor_kind": claims.actor_kind,
            "org_id": claims.org_id,
            "exp": claims.exp,
            "credential_id": claims.credential_id,
        }

        for bag in candidates:
            for key in _PROTECTED_IDENTITY_KEYS:
                if key not in bag:
                    continue
                provided = bag[key]
                if key == "scopes":
                    if isinstance(provided, str):
                        provided_set = {provided}
                    elif isinstance(provided, Iterable):
                        provided_set = {str(s) for s in provided}
                    else:
                        raise AuthError(
                            "auth_spoof_rejected",
                            "Spoofed identity rejected: invalid scopes type",
                        )
                    if provided_set != set(claims.scopes):
                        raise AuthError(
                            "auth_spoof_rejected",
                            "Spoofed identity rejected: scopes mismatch",
                        )
                    continue

                expected_value = expected.get(key)
                if expected_value == "":
                    # credential_id optional on claim side; still reject mismatch
                    # when both sides present and differ.
                    if str(provided) and str(provided) != str(expected_value):
                        # If verifier claim has empty credential_id, any provided
                        # value is treated as spoof attempt to inject identity.
                        raise AuthError(
                            "auth_spoof_rejected",
                            f"Spoofed identity rejected: {key} must not be supplied",
                        )
                    continue

                if str(provided) != str(expected_value):
                    raise AuthError(
                        "auth_spoof_rejected",
                        f"Spoofed identity rejected: {key} mismatch",
                    )


def mint_fake_token(claims: Mapping[str, Any]) -> str:
    """Helper for tests: mint a ``fake.<b64>`` bearer token."""
    payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return f"fake.{encoded}"
