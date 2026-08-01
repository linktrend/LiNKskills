"""Same-origin, no-redirect JWKS client for PACI ES256 verification.

**Evidence class:** local/fake conformance against frozen
``platform.auth-token-envelope/0.1.0``; not live-proven against Platform PACI.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Protocol
from urllib.parse import urlparse

from .auth import AuthError
from .paci_types import (
    AUTH_MODE_LOCAL_TEST,
    JWKS_CACHE_TTL_SECONDS,
    LOCAL_TEST_LOOPBACK_HOSTS,
    PACI_ALG,
)


FetchFn = Callable[[str], bytes]


class JwksKeyProvider(Protocol):
    """Lookup public JWK material by ``kid`` for PACI signature verification."""

    def get_key(self, kid: str) -> Mapping[str, Any]:
        """Return a single JWK dict for ``kid`` or raise AuthError."""

    def purge_kid(self, kid: str) -> None:
        """Drop cached material for ``kid`` (revocation / rotation signal)."""

    def purge_all(self) -> None:
        """Drop the entire JWKS cache."""


def assert_https_transport(
    url: str,
    *,
    label: str,
    auth_mode: str = "production",
) -> None:
    """Require HTTPS except explicit local-test loopback HTTP."""
    parsed = urlparse(str(url).strip())
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    if scheme == "https":
        return
    if (
        scheme == "http"
        and auth_mode == AUTH_MODE_LOCAL_TEST
        and host in LOCAL_TEST_LOOPBACK_HOSTS
    ):
        return
    raise AuthError(
        "auth_https_required",
        f"{label} must use HTTPS in non-test environments "
        f"(got {scheme!r}://{host or ''}); "
        f"HTTP only when LINKSKILLS_AUTH_MODE=local-test AND loopback host",
    )


def assert_same_origin(issuer: str, jwks_uri: str) -> None:
    """Require ``jwks_uri`` origin == ``issuer`` origin (scheme+host+port)."""
    iss = urlparse(issuer)
    jwks = urlparse(jwks_uri)
    if iss.scheme not in {"https", "http"} or jwks.scheme not in {"https", "http"}:
        raise AuthError(
            "jwks_origin_rejected",
            f"issuer/jwks_uri must use http(s); got {iss.scheme!r}/{jwks.scheme!r}",
        )
    if iss.scheme != jwks.scheme:
        raise AuthError(
            "jwks_origin_rejected",
            f"jwks_uri scheme {jwks.scheme!r} != issuer scheme {iss.scheme!r}",
        )
    if (iss.hostname or "").lower() != (jwks.hostname or "").lower():
        raise AuthError(
            "jwks_origin_rejected",
            f"jwks_uri host {jwks.hostname!r} != issuer host {iss.hostname!r}",
        )
    iss_port = iss.port or (443 if iss.scheme == "https" else 80)
    jwks_port = jwks.port or (443 if jwks.scheme == "https" else 80)
    if iss_port != jwks_port:
        raise AuthError(
            "jwks_origin_rejected",
            f"jwks_uri port {jwks_port} != issuer port {iss_port}",
        )


def validate_issuer_identifier(
    issuer: str,
    *,
    auth_mode: str = "production",
) -> None:
    """Phase-1: issuer must be absolute URI, no trailing slash, no path."""
    text = str(issuer).strip()
    if not text:
        raise AuthError("auth_config", "PACI issuer is required")
    if text.endswith("/"):
        raise AuthError(
            "auth_config",
            "PACI issuer must not end with '/' (Phase-1 root issuer rule)",
        )
    parsed = urlparse(text)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise AuthError("auth_config", f"PACI issuer must be absolute URI: {text!r}")
    if parsed.path not in {"", "/"}:
        raise AuthError(
            "auth_config",
            "PACI Phase-1 issuer must not contain a non-empty path",
        )
    assert_https_transport(text, label="PACI issuer", auth_mode=auth_mode)


def _validate_ec_p256_jwk(jwk: Mapping[str, Any], *, kid: str) -> None:
    kty = str(jwk.get("kty") or "")
    if kty != "EC":
        raise AuthError("jwks_invalid", f"JWKS kid={kid!r}: kty must be EC")
    crv = str(jwk.get("crv") or "")
    if crv != "P-256":
        raise AuthError("jwks_invalid", f"JWKS kid={kid!r}: crv must be P-256")
    alg = jwk.get("alg")
    if alg is not None and str(alg) != PACI_ALG:
        raise AuthError(
            "jwks_invalid",
            f"JWKS kid={kid!r}: alg must be {PACI_ALG} or absent",
        )
    use = jwk.get("use")
    if use is not None and str(use) != "sig":
        raise AuthError("jwks_invalid", f"JWKS kid={kid!r}: use must be 'sig' or absent")
    key_ops = jwk.get("key_ops")
    if key_ops is not None:
        if not isinstance(key_ops, list):
            raise AuthError("jwks_invalid", f"JWKS kid={kid!r}: key_ops must be array")
        ops = {str(x) for x in key_ops}
        if "verify" not in ops:
            raise AuthError(
                "jwks_invalid",
                f"JWKS kid={kid!r}: key_ops must include 'verify'",
            )
        if "sign" in ops:
            raise AuthError(
                "jwks_invalid",
                f"JWKS kid={kid!r}: published public keys must not include 'sign'",
            )
    if not jwk.get("x") or not jwk.get("y"):
        raise AuthError("jwks_invalid", f"JWKS kid={kid!r}: missing EC x/y")


def index_jwks_keys(document: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    """Index JWKS keys by kid; reject collisions and invalid EC keys."""
    keys = document.get("keys")
    if not isinstance(keys, list) or not keys:
        raise AuthError("jwks_invalid", "JWKS document missing non-empty 'keys'")
    indexed: Dict[str, Mapping[str, Any]] = {}
    for item in keys:
        if not isinstance(item, Mapping):
            raise AuthError("jwks_invalid", "JWKS key entry must be an object")
        kid = str(item.get("kid") or "").strip()
        if not kid:
            raise AuthError("jwks_invalid", "JWKS key missing kid")
        if kid in indexed:
            raise AuthError(
                "jwks_kid_collision",
                f"JWKS contains duplicate kid={kid!r}; reject fail-closed",
            )
        _validate_ec_p256_jwk(item, kid=kid)
        indexed[kid] = dict(item)
    return indexed


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject all HTTP redirects (SSRF / key-selection hardening)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise AuthError(
            "jwks_redirect_rejected",
            f"JWKS fetch redirected ({code}) to {newurl!r}; redirects forbidden",
        )


def default_jwks_fetch(url: str, *, timeout: float = 5.0) -> bytes:
    """HTTP GET without following redirects."""
    opener = urllib.request.build_opener(_NoRedirectHandler())
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "linkskills-paci-jwks/0.1"},
    )
    try:
        with opener.open(request, timeout=timeout) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            if int(status) != 200:
                raise AuthError(
                    "jwks_fetch_failed",
                    f"JWKS HTTP {status} from {url}",
                )
            return resp.read()
    except AuthError:
        raise
    except urllib.error.HTTPError as exc:
        raise AuthError(
            "jwks_fetch_failed",
            f"JWKS HTTP {exc.code} from {url}",
        ) from exc
    except Exception as exc:  # noqa: BLE001 — network boundary
        raise AuthError("jwks_fetch_failed", f"JWKS fetch failed: {exc}") from exc


@dataclass
class _JwksCache:
    keys: Dict[str, Mapping[str, Any]] = field(default_factory=dict)
    fetched_at: float = 0.0

    def is_fresh(self, now: float, ttl: float) -> bool:
        if not self.keys or self.fetched_at <= 0:
            return False
        return (now - self.fetched_at) <= ttl


class CachedJwksClient:
    """Pinned-issuer JWKS client with ≤5min cache and fail-closed outage rules.

    Outage: if fetch fails, continue using a still-valid cache until TTL expiry.
    Once no usable cached key remains for the required kid, fail closed.
    """

    def __init__(
        self,
        *,
        issuer: str,
        jwks_uri: str,
        fetch_fn: Optional[FetchFn] = None,
        cache_ttl_seconds: float = JWKS_CACHE_TTL_SECONDS,
        now_fn: Optional[Callable[[], float]] = None,
        initial_document: Optional[Mapping[str, Any]] = None,
        auth_mode: str = "production",
    ) -> None:
        validate_issuer_identifier(issuer, auth_mode=auth_mode)
        assert_https_transport(jwks_uri, label="PACI jwks_uri", auth_mode=auth_mode)
        assert_same_origin(issuer, jwks_uri)
        if cache_ttl_seconds <= 0 or cache_ttl_seconds > JWKS_CACHE_TTL_SECONDS:
            # Allow shorter TTL in tests; never exceed envelope bound.
            if cache_ttl_seconds > JWKS_CACHE_TTL_SECONDS:
                raise AuthError(
                    "auth_config",
                    f"JWKS cache TTL must be ≤ {JWKS_CACHE_TTL_SECONDS}s",
                )
            if cache_ttl_seconds <= 0:
                raise AuthError("auth_config", "JWKS cache TTL must be positive")
        self.issuer = issuer
        self.jwks_uri = jwks_uri
        self._fetch = fetch_fn or default_jwks_fetch
        self._ttl = float(cache_ttl_seconds)
        self._now = now_fn or time.time
        self._cache = _JwksCache()
        if initial_document is not None:
            self._cache = _JwksCache(
                keys=index_jwks_keys(initial_document),
                fetched_at=self._now(),
            )

    def get_key(self, kid: str) -> Mapping[str, Any]:
        kid = str(kid).strip()
        if not kid:
            raise AuthError("auth_invalid", "JWT header kid is required")
        now = float(self._now())
        if self._cache.is_fresh(now, self._ttl) and kid in self._cache.keys:
            return self._cache.keys[kid]

        # Refresh when cache miss or stale.
        try:
            self._refresh(now=now)
        except AuthError as fetch_err:
            # Outage path: use still-valid cache only.
            if self._cache.is_fresh(now, self._ttl) and kid in self._cache.keys:
                return self._cache.keys[kid]
            if self._cache.is_fresh(now, self._ttl):
                raise AuthError(
                    "jwks_unknown_kid",
                    f"Unknown kid={kid!r} in cached JWKS (fetch also failed)",
                ) from fetch_err
            raise AuthError(
                "jwks_unavailable",
                f"JWKS unavailable and no usable cache for kid={kid!r}: "
                f"{fetch_err.message}",
            ) from fetch_err

        if kid not in self._cache.keys:
            raise AuthError("jwks_unknown_kid", f"Unknown kid={kid!r} in JWKS")
        return self._cache.keys[kid]

    def purge_kid(self, kid: str) -> None:
        kid = str(kid).strip()
        self._cache.keys.pop(kid, None)

    def purge_all(self) -> None:
        self._cache = _JwksCache()

    def _refresh(self, *, now: float) -> None:
        raw = self._fetch(self.jwks_uri)
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AuthError("jwks_invalid", "JWKS response is not valid JSON") from exc
        if not isinstance(document, Mapping):
            raise AuthError("jwks_invalid", "JWKS root must be an object")
        keys = index_jwks_keys(document)
        self._cache = _JwksCache(keys=keys, fetched_at=now)


class StaticJwksProvider:
    """In-memory JWKS provider for tests (no network)."""

    def __init__(self, document: Mapping[str, Any]) -> None:
        self._keys = index_jwks_keys(document)

    def get_key(self, kid: str) -> Mapping[str, Any]:
        kid = str(kid).strip()
        if kid not in self._keys:
            raise AuthError("jwks_unknown_kid", f"Unknown kid={kid!r} in JWKS")
        return self._keys[kid]

    def purge_kid(self, kid: str) -> None:
        self._keys.pop(str(kid).strip(), None)

    def purge_all(self) -> None:
        self._keys.clear()

    def as_document(self) -> Dict[str, List[Mapping[str, Any]]]:
        return {"keys": list(self._keys.values())}
