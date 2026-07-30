"""RFC 7662 token introspection client for PACI high-risk writes.

**Evidence class:** implemented but not proven against frozen Platform PACI
service (envelope ``platform.auth-token-envelope/0.1.3-draft``).

Caller authentication uses ``private_key_jwt`` via an injectable assertion
signer stub — Skills does not hold Platform signing keys in this adapter.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional, Protocol

from .auth import AuthError
from .paci_types import INTROSPECTION_CACHE_TTL_SECONDS


class ClientAssertionSigner(Protocol):
    """Mint a short-lived private_key_jwt client assertion for introspection.

    Production: Platform-approved client key via secret injection.
    Tests: ephemeral local signer (fake_local evidence).
    """

    def mint_assertion(self, *, audience: str, client_id: str) -> str:
        """Return a compact JWS client assertion (aud = introspection endpoint)."""


@dataclass(frozen=True)
class IntrospectionResult:
    """Parsed active introspection response (RFC 7662 + PACI fields)."""

    active: bool
    raw: Mapping[str, Any] = field(default_factory=dict)
    jti: str = ""
    iss: str = ""
    sub: str = ""
    client_id: str = ""
    credential_id: str = ""
    runtime_binding_id: str = ""


FetchIntrospectionFn = Callable[[str, Mapping[str, str], bytes], tuple[int, bytes]]


def default_introspection_fetch(
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    *,
    timeout: float = 5.0,
) -> tuple[int, bytes]:
    """POST form-urlencoded introspection request (no redirect follow)."""
    from .jwks import _NoRedirectHandler

    opener = urllib.request.build_opener(_NoRedirectHandler())
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers=dict(headers),
    )
    try:
        with opener.open(request, timeout=timeout) as resp:
            status = int(getattr(resp, "status", None) or resp.getcode())
            return status, resp.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read() if exc.fp else b""
    except Exception as exc:  # noqa: BLE001
        raise AuthError(
            "introspection_unavailable",
            f"Introspection endpoint unreachable: {exc}",
        ) from exc


@dataclass
class _CacheEntry:
    result: IntrospectionResult
    stored_at: float


class IntrospectionClient:
    """RFC 7662 client with ≤30s jti cache; fail-closed on down/401/inactive.

    High-risk writes require HTTP 200 + ``active: true``.
    """

    def __init__(
        self,
        *,
        introspection_url: str,
        client_id: str,
        assertion_signer: ClientAssertionSigner,
        fetch_fn: Optional[FetchIntrospectionFn] = None,
        cache_ttl_seconds: float = INTROSPECTION_CACHE_TTL_SECONDS,
        now_fn: Optional[Callable[[], float]] = None,
        resource_client_id: Optional[str] = None,
    ) -> None:
        url = str(introspection_url).strip()
        if not url:
            raise AuthError("auth_config", "introspection_url is required")
        if cache_ttl_seconds <= 0 or cache_ttl_seconds > INTROSPECTION_CACHE_TTL_SECONDS:
            if cache_ttl_seconds > INTROSPECTION_CACHE_TTL_SECONDS:
                raise AuthError(
                    "auth_config",
                    f"Introspection cache TTL must be ≤ {INTROSPECTION_CACHE_TTL_SECONDS}s",
                )
            raise AuthError("auth_config", "Introspection cache TTL must be positive")
        self.introspection_url = url
        self.client_id = str(client_id).strip()
        if not self.client_id:
            raise AuthError("auth_config", "introspection client_id is required")
        self.assertion_signer = assertion_signer
        self._fetch = fetch_fn or default_introspection_fetch
        self._ttl = float(cache_ttl_seconds)
        self._now = now_fn or time.time
        # Cache key = jti + resource client (envelope §7.4).
        self._resource_client_id = str(resource_client_id or self.client_id).strip()
        self._cache: Dict[str, _CacheEntry] = {}

    def _cache_key(self, jti: str) -> str:
        return f"{jti}::{self._resource_client_id}"

    def purge_jti(self, jti: str) -> None:
        self._cache.pop(self._cache_key(jti), None)

    def purge_all(self) -> None:
        self._cache.clear()

    def introspect(
        self,
        access_token: str,
        *,
        jti: Optional[str] = None,
        force_refresh: bool = False,
    ) -> IntrospectionResult:
        """Introspect an access token; require active for callers that enforce it."""
        token = str(access_token).strip()
        if not token:
            raise AuthError("auth_missing", "token required for introspection")

        cache_jti = str(jti or "").strip()
        now = float(self._now())
        if cache_jti and not force_refresh:
            entry = self._cache.get(self._cache_key(cache_jti))
            if entry is not None and (now - entry.stored_at) <= self._ttl:
                return entry.result

        assertion = self.assertion_signer.mint_assertion(
            audience=self.introspection_url,
            client_id=self.client_id,
        )
        form = urllib.parse.urlencode(
            {
                "token": token,
                "token_type_hint": "access_token",
                "client_id": self.client_id,
                "client_assertion_type": (
                    "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
                ),
                "client_assertion": assertion,
            }
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "linkskills-paci-introspect/0.1",
        }

        try:
            status, raw = self._fetch(self.introspection_url, headers, form)
        except AuthError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise AuthError(
                "introspection_unavailable",
                f"Introspection down: {exc}",
            ) from exc

        if status == 401:
            raise AuthError(
                "introspection_unauthorized",
                "Introspection client authentication rejected (HTTP 401)",
            )
        if status != 200:
            raise AuthError(
                "introspection_unavailable",
                f"Introspection HTTP {status}; fail-closed for high-risk writes",
            )

        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AuthError(
                "introspection_invalid",
                "Introspection response is not valid JSON",
            ) from exc
        if not isinstance(body, dict):
            raise AuthError(
                "introspection_invalid",
                "Introspection response must be a JSON object",
            )

        active = body.get("active")
        if active is not True:
            # 200 + active:false (or missing) ⇒ inactive / deny
            raise AuthError(
                "auth_revoked",
                "Token inactive per introspection (active != true)",
            )

        result = IntrospectionResult(
            active=True,
            raw=dict(body),
            jti=str(body.get("jti") or cache_jti or "").strip(),
            iss=str(body.get("iss") or "").strip(),
            sub=str(body.get("sub") or "").strip(),
            client_id=str(body.get("client_id") or "").strip(),
            credential_id=str(body.get("credential_id") or "").strip(),
            runtime_binding_id=str(body.get("runtime_binding_id") or "").strip(),
        )
        store_jti = result.jti or cache_jti
        if store_jti:
            self._cache[self._cache_key(store_jti)] = _CacheEntry(
                result=result, stored_at=now
            )
        return result

    def require_active(
        self,
        access_token: str,
        *,
        jti: str,
        expected_sub: Optional[str] = None,
        expected_credential_id: Optional[str] = None,
        expected_runtime_binding_id: Optional[str] = None,
    ) -> IntrospectionResult:
        """High-risk gate: 200 + active:true (+ optional id matching)."""
        result = self.introspect(access_token, jti=jti)
        if expected_sub and result.sub and result.sub != expected_sub:
            raise AuthError(
                "auth_forbidden",
                "Introspection sub mismatch vs JWT/AuthClaims",
            )
        if (
            expected_credential_id
            and result.credential_id
            and result.credential_id != expected_credential_id
        ):
            raise AuthError(
                "auth_forbidden",
                "Introspection credential_id mismatch",
            )
        if (
            expected_runtime_binding_id
            and result.runtime_binding_id
            and result.runtime_binding_id != expected_runtime_binding_id
        ):
            raise AuthError(
                "auth_forbidden",
                "Introspection runtime_binding_id mismatch",
            )
        return result


class StubClientAssertionSigner:
    """Test/dev stub that emits opaque non-cryptographic assertion placeholders.

    Production must inject a real private_key_jwt signer. This stub exists so
    the introspection client interface is complete without shipping keys.
    """

    def mint_assertion(self, *, audience: str, client_id: str) -> str:
        # Opaque placeholder — not a valid JWT; only for DI wiring tests that
        # mock the HTTP fetch layer.
        return (
            f"stub-assertion.{client_id}.{uuid.uuid4().hex}."
            f"{urllib.parse.quote(audience, safe='')}"
        )
