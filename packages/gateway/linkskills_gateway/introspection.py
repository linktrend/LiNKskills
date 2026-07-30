"""RFC 7662 token introspection client for PACI high-risk writes.

**Evidence class:** local/fake conformance against frozen
``platform.auth-token-envelope/0.1.0``; not live-proven against Platform PACI.

Caller authentication uses ``private_key_jwt`` via SecretRef-backed signer.
``LocalTestClientAssertionSigner`` exists only behind the explicit local-test
gate (``LINKSKILLS_AUTH_MODE=local-test``) and must never be constructed on
production/stage paths.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Protocol, Sequence, Set

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from .auth import AuthError
from .jwks import assert_https_transport
from .paci_types import (
    AUTH_MODE_LOCAL_TEST,
    CLIENT_ASSERTION_LIFETIME_MAX_S,
    ENV_PACI_CLIENT_KID,
    ENV_PACI_CLIENT_PRIVATE_KEY_FILE,
    INTROSPECTION_CACHE_TTL_SECONDS,
    LOCAL_TEST_ASSERTION_SIGNER_GATE,
)


class ClientAssertionSigner(Protocol):
    """Mint a short-lived private_key_jwt client assertion for introspection.

    Production: Platform-approved client key via SecretRef file.
    Local-test only: ``LocalTestClientAssertionSigner`` behind explicit gate.
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
    aud: frozenset[str] = field(default_factory=frozenset)
    client_id: str = ""
    credential_id: str = ""
    runtime_binding_id: str = ""
    iat: int = 0
    exp: int = 0
    token_type: str = ""
    scope: str = ""


FetchIntrospectionFn = Callable[[str, Mapping[str, str], bytes], tuple[int, bytes]]

# Required fields on active:true responses (missing ⇒ deny).
_ACTIVE_REQUIRED_FIELDS = frozenset(
    {
        "active",
        "iss",
        "aud",
        "sub",
        "client_id",
        "credential_id",
        "runtime_binding_id",
        "jti",
        "iat",
        "exp",
        "token_type",
        "scope",
    }
)


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


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _as_aud_set(value: Any) -> Set[str]:
    if isinstance(value, str):
        raise AuthError(
            "introspection_invalid",
            "Introspection aud must be an array (string form rejected)",
        )
    if not isinstance(value, list) or not value:
        raise AuthError(
            "introspection_invalid",
            "Introspection aud must be a non-empty array",
        )
    out: Set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise AuthError(
                "introspection_invalid",
                "Introspection aud entries must be non-empty strings",
            )
        out.add(item.strip())
    return out


@dataclass
class _CacheEntry:
    result: IntrospectionResult
    stored_at: float


class IntrospectionClient:
    """RFC 7662 client with ≤30s jti cache; fail-closed on down/401/inactive.

    High-risk writes require HTTP 200 + ``active: true`` with exact binding.
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
        auth_mode: str = "production",
        required_scopes: Optional[Sequence[str]] = None,
    ) -> None:
        url = str(introspection_url).strip()
        if not url:
            raise AuthError("auth_config", "introspection_url is required")
        assert_https_transport(
            url, label="PACI introspection_url", auth_mode=auth_mode
        )
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
        if isinstance(assertion_signer, LocalTestClientAssertionSigner):
            if auth_mode != AUTH_MODE_LOCAL_TEST:
                raise AuthError(
                    "auth_config",
                    "LocalTestClientAssertionSigner is forbidden outside "
                    f"{LOCAL_TEST_ASSERTION_SIGNER_GATE}",
                )
        self.assertion_signer = assertion_signer
        self._fetch = fetch_fn or default_introspection_fetch
        self._ttl = float(cache_ttl_seconds)
        self._now = now_fn or time.time
        # Cache key = jti + resource client (envelope §7.4).
        self._resource_client_id = str(resource_client_id or self.client_id).strip()
        self._cache: Dict[str, _CacheEntry] = {}
        self._required_scopes = frozenset(
            str(s).strip() for s in (required_scopes or ()) if str(s).strip()
        )

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
            # 200 + active:false (or missing) ⇒ inactive / deny.
            # Privacy: do not echo inactive response fields.
            raise AuthError(
                "auth_revoked",
                "Token inactive per introspection (active != true)",
            )

        missing = sorted(_ACTIVE_REQUIRED_FIELDS - set(body.keys()))
        if missing:
            raise AuthError(
                "introspection_invalid",
                "active:true response missing required field(s): "
                + ", ".join(missing),
            )

        try:
            aud = frozenset(_as_aud_set(body.get("aud")))
        except AuthError:
            raise

        iat = body.get("iat")
        exp = body.get("exp")
        if isinstance(iat, bool) or not isinstance(iat, int):
            raise AuthError(
                "introspection_invalid",
                "Introspection iat must be whole-second integer",
            )
        if isinstance(exp, bool) or not isinstance(exp, int):
            raise AuthError(
                "introspection_invalid",
                "Introspection exp must be whole-second integer",
            )

        token_type = body.get("token_type")
        if token_type != "Bearer":
            raise AuthError(
                "introspection_invalid",
                f"Introspection token_type must be 'Bearer', got {token_type!r}",
            )

        result = IntrospectionResult(
            active=True,
            raw=dict(body),
            jti=str(body.get("jti") or "").strip(),
            iss=str(body.get("iss") or "").strip(),
            sub=str(body.get("sub") or "").strip(),
            aud=aud,
            client_id=str(body.get("client_id") or "").strip(),
            credential_id=str(body.get("credential_id") or "").strip(),
            runtime_binding_id=str(body.get("runtime_binding_id") or "").strip(),
            iat=iat,
            exp=exp,
            token_type="Bearer",
            scope=str(body.get("scope") or "").strip(),
        )
        # Empty required string fields ⇒ deny (no truthiness shortcuts later).
        for field_name, value in (
            ("jti", result.jti),
            ("iss", result.iss),
            ("sub", result.sub),
            ("client_id", result.client_id),
            ("credential_id", result.credential_id),
            ("runtime_binding_id", result.runtime_binding_id),
            ("scope", result.scope),
        ):
            if not value:
                raise AuthError(
                    "introspection_invalid",
                    f"active:true response field {field_name!r} is empty",
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
        expected_iss: str,
        expected_aud: Sequence[str],
        expected_sub: str,
        trusted_mint_client_ids: Sequence[str],
        expected_credential_id: str,
        expected_runtime_binding_id: str,
        expected_iat: int,
        expected_exp: int,
        required_scopes: Optional[Sequence[str]] = None,
    ) -> IntrospectionResult:
        """High-risk gate: 200 + active:true with exact binding (no shortcuts).

        ``client_id`` on an active response is the **access-token mint** client
        identity. It is validated against ``trusted_mint_client_ids``, never
        against this client's private_key_jwt assertion ``client_id`` (RS
        introspect caller identity).
        """
        result = self.introspect(access_token, jti=jti)

        # Always require and exactly match — missing/empty already denied above.
        if result.iss != expected_iss:
            raise AuthError(
                "auth_forbidden",
                "Introspection iss mismatch vs JWT",
            )
        expected_aud_set = {str(a).strip() for a in expected_aud if str(a).strip()}
        if set(result.aud) != expected_aud_set:
            raise AuthError(
                "auth_forbidden",
                "Introspection aud set mismatch vs JWT",
            )
        if result.sub != expected_sub:
            raise AuthError(
                "auth_forbidden",
                "Introspection sub mismatch vs JWT/AuthClaims",
            )
        allowed_mint_ids = frozenset(
            str(c).strip() for c in trusted_mint_client_ids if str(c).strip()
        )
        if not allowed_mint_ids:
            raise AuthError(
                "auth_config",
                "trusted mint client_id allow-list is empty; fail-closed",
            )
        if result.client_id not in allowed_mint_ids:
            raise AuthError(
                "auth_forbidden",
                "Introspection client_id not in trusted mint allow-list",
            )
        if result.credential_id != expected_credential_id:
            raise AuthError(
                "auth_forbidden",
                "Introspection credential_id mismatch",
            )
        if result.runtime_binding_id != expected_runtime_binding_id:
            raise AuthError(
                "auth_forbidden",
                "Introspection runtime_binding_id mismatch",
            )
        if result.jti != jti:
            raise AuthError(
                "auth_forbidden",
                "Introspection jti mismatch vs JWT",
            )
        if result.iat != expected_iat:
            raise AuthError(
                "auth_forbidden",
                "Introspection iat mismatch vs JWT",
            )
        if result.exp != expected_exp:
            raise AuthError(
                "auth_forbidden",
                "Introspection exp mismatch vs JWT",
            )
        if result.token_type != "Bearer":
            raise AuthError(
                "auth_forbidden",
                "Introspection token_type must be Bearer",
            )

        scopes_needed = frozenset(
            str(s).strip()
            for s in (required_scopes if required_scopes is not None else self._required_scopes)
            if str(s).strip()
        )
        have_scopes = {part for part in result.scope.split() if part}
        if scopes_needed and not scopes_needed.issubset(have_scopes):
            raise AuthError(
                "auth_forbidden",
                "Introspection scope missing required value(s): "
                + ", ".join(sorted(scopes_needed - have_scopes)),
            )
        return result


class SecretRefClientAssertionSigner:
    """Real ``private_key_jwt`` signer backed by a SecretRef PEM file path."""

    def __init__(
        self,
        *,
        private_key_file: Path | str,
        kid: Optional[str] = None,
        assertion_lifetime_s: int = CLIENT_ASSERTION_LIFETIME_MAX_S,
        now_fn: Optional[Callable[[], float]] = None,
    ) -> None:
        path = Path(private_key_file)
        if not path.is_file():
            raise AuthError(
                "auth_config",
                f"private_key_jwt SecretRef file missing ({ENV_PACI_CLIENT_PRIVATE_KEY_FILE})",
            )
        if assertion_lifetime_s < 1 or assertion_lifetime_s > CLIENT_ASSERTION_LIFETIME_MAX_S:
            raise AuthError(
                "auth_config",
                f"assertion_lifetime_s must be 1..{CLIENT_ASSERTION_LIFETIME_MAX_S}",
            )
        try:
            raw = path.read_bytes()
            key = serialization.load_pem_private_key(raw, password=None)
        except AuthError:
            raise
        except Exception as exc:  # noqa: BLE001 — fail closed, no key detail
            raise AuthError(
                "auth_config",
                "private_key_jwt SecretRef file is not a usable EC P-256 PEM key",
            ) from exc
        if not isinstance(key, ec.EllipticCurvePrivateKey):
            raise AuthError(
                "auth_config",
                "private_key_jwt key must be EC (ES256 / P-256)",
            )
        if not isinstance(key.curve, ec.SECP256R1):
            raise AuthError(
                "auth_config",
                "private_key_jwt key curve must be P-256 (SECP256R1)",
            )
        self._private_key = key
        self._kid = str(kid).strip() if kid else None
        self._lifetime = int(assertion_lifetime_s)
        self._now = now_fn or time.time
        self._used_jtis: Dict[str, float] = {}

    @classmethod
    def from_environ(
        cls,
        environ: Mapping[str, str],
        *,
        now_fn: Optional[Callable[[], float]] = None,
    ) -> "SecretRefClientAssertionSigner":
        key_file = str(environ.get(ENV_PACI_CLIENT_PRIVATE_KEY_FILE) or "").strip()
        if not key_file:
            raise AuthError(
                "auth_config",
                "Production/stage PACI introspection requires "
                f"{ENV_PACI_CLIENT_PRIVATE_KEY_FILE} SecretRef file "
                "(real private_key_jwt signer); stub signer forbidden",
            )
        kid = str(environ.get(ENV_PACI_CLIENT_KID) or "").strip() or None
        return cls(private_key_file=key_file, kid=kid, now_fn=now_fn)

    def mint_assertion(self, *, audience: str, client_id: str) -> str:
        now = int(self._now())
        exp = now + self._lifetime
        # Drop expired local assertion jtis; reject reuse of still-valid ones.
        expired = [j for j, until in self._used_jtis.items() if until <= now]
        for j in expired:
            del self._used_jtis[j]
        jti = str(uuid.uuid4())
        if jti in self._used_jtis:
            raise AuthError(
                "auth_assertion_replay",
                "Client assertion jti collision (local replay reject)",
            )
        self._used_jtis[jti] = float(exp)
        header: Dict[str, Any] = {"alg": "ES256", "typ": "JWT"}
        if self._kid:
            header["kid"] = self._kid
        claims = {
            "iss": client_id,
            "sub": client_id,
            "aud": audience,
            "iat": now,
            "exp": exp,
            "jti": jti,
        }
        signing_input = (
            f"{_b64url(json.dumps(header, separators=(',', ':')).encode('utf-8'))}."
            f"{_b64url(json.dumps(claims, separators=(',', ':')).encode('utf-8'))}"
        ).encode("ascii")
        der_sig = self._private_key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(der_sig)
        raw_sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        return f"{signing_input.decode('ascii')}.{_b64url(raw_sig)}"

    def remember_assertion_jti(self, jti: str, *, until: float) -> None:
        """Test helper: mark a jti as used to prove local replay rejection."""
        if jti in self._used_jtis and self._used_jtis[jti] > self._now():
            raise AuthError(
                "auth_assertion_replay",
                "Client assertion jti already used (replay reject)",
            )
        self._used_jtis[jti] = until


class LocalTestClientAssertionSigner:
    """Opaque assertion placeholder for DI wiring under local-test gate only.

    Gate: ``LINKSKILLS_AUTH_MODE=local-test``. Never construct on
    production/stage paths (``IntrospectionClient`` / factory enforce this).
    """

    def __init__(self, *, auth_mode: str = AUTH_MODE_LOCAL_TEST) -> None:
        if auth_mode != AUTH_MODE_LOCAL_TEST:
            raise AuthError(
                "auth_config",
                "LocalTestClientAssertionSigner requires "
                f"{LOCAL_TEST_ASSERTION_SIGNER_GATE}",
            )

    def mint_assertion(self, *, audience: str, client_id: str) -> str:
        return (
            f"local-test-assertion.{client_id}.{uuid.uuid4().hex}."
            f"{urllib.parse.quote(audience, safe='')}"
        )


# Backward-compatible alias for tests that still import the historical name.
# Construction still requires the local-test gate via LocalTestClientAssertionSigner.
StubClientAssertionSigner = LocalTestClientAssertionSigner
