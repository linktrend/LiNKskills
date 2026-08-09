"""PACI ``client_credentials`` + ``private_key_jwt`` (ES256) for LiNKskills only.

Consumer of Platform frozen ``platform.auth-token-envelope/0.1.0`` §§6–7:

- Assertion: ``iss``/``sub`` = ``client_id``, ``aud`` = token_endpoint,
  ``iat``, ``exp`` ≤ 5 minutes, ``jti`` UUID (locally replay-tracked).
- Mint: ``access_token`` + ``token_type=Bearer`` + ``expires_in``;
  expected access lifetime 15 minutes; **no** ``refresh_token`` handling.
- Early renewal when remaining TTL < 20% of lifetime.
- Bounded retry/backoff on transient failures; fail closed on auth errors.
- Private key via a SecretRef file path or one inherited file descriptor
  (``LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FD``) — never CLI args; never logged.
- Audience/endpoint pinned for Skills; Brain/OpenClaw reuse helpers refused.

**Mark:** Skills-owned Cursor path implemented locally; not live-proven
(Platform PACI issuer absent).
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

logger = logging.getLogger(__name__)

CLIENT_ASSERTION_TYPE = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
ASSERTION_LIFETIME_MAX_S = 300  # §6.2 exp ≤ 5 minutes
EXPECTED_ACCESS_TTL_S = 900  # §6.4 phase-1: 15 minutes
MAX_ACCESS_TTL_S = 900  # frozen envelope: reject mint expires_in above this
EARLY_RENEWAL_FRACTION = 0.20
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE_S = 0.25
DEFAULT_TIMEOUT_S = 15.0
GATEWAY_401_RETRY_MAX = 1  # invalidate + remint once on resource-server 401
MAX_PRIVATE_KEY_BYTES = 64 * 1024

# Env SecretRef / config keys (no secret values)
ENV_CLIENT_ID = "LINKSKILLS_PACI_CLIENT_ID"
ENV_TOKEN_ENDPOINT = "LINKSKILLS_PACI_TOKEN_ENDPOINT"
ENV_PRIVATE_KEY_FILE = "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE"
ENV_PRIVATE_KEY_FD = "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FD"
ENV_KID = "LINKSKILLS_PACI_CLIENT_KID"
ENV_SCOPE = "LINKSKILLS_PACI_SCOPE"
ENV_RESOURCE_AUDIENCE = "LINKSKILLS_PACI_RESOURCE_AUDIENCE"
ENV_AUTH_MODE = "LINKSKILLS_AUTH_MODE"

AUTH_MODE_LOCAL_TEST = "local-test"
AUTH_MODE_PRODUCTION = "production"

# Substrings that mark non-Skills domains — refuse reuse helpers / mispins.
_FORBIDDEN_DOMAIN_MARKERS: Sequence[str] = (
    "linkbrain",
    "lnkbrain",
    "lbrain",
    "/brain",
    "brain.",
    "openclaw",
    "lisa-gateway",
    "lisa.",
)


class PaciTokenError(RuntimeError):
    """Base PACI token-client failure (fail closed)."""


class PaciAuthError(PaciTokenError):
    """Non-retryable authentication / authorization failure."""


class PaciTransientError(PaciTokenError):
    """Transient transport or 5xx failure (may retry)."""


class PaciConfigError(PaciTokenError):
    """Invalid or cross-domain Skills PACI configuration."""


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _contains_forbidden_marker(value: str) -> Optional[str]:
    lowered = value.lower()
    for marker in _FORBIDDEN_DOMAIN_MARKERS:
        if marker in lowered:
            return marker
    return None


def refuse_brain_openclaw_reuse(*, purpose: str = "PACI client") -> None:
    """Explicit refuse helper — Brain/OpenClaw must not reuse Skills PACI clients.

    Call sites that might be tempted to share a Skills machine credential with
    Brain or OpenClaw must invoke this (or hit config validation) and stop.
    """
    raise PaciConfigError(
        f"{purpose}: Skills PACI credentials/endpoints must not be reused for "
        "Brain or OpenClaw. Register a separate client_id, audience, and "
        "credential per domain (platform.auth-token-envelope §6.1)."
    )


def _assert_skills_pinned(label: str, value: str) -> None:
    if not value or not str(value).strip():
        raise PaciConfigError(f"{label} is required and must be Skills-pinned")
    marker = _contains_forbidden_marker(value)
    if marker is not None:
        raise PaciConfigError(
            f"{label} refuses Brain/OpenClaw reuse (matched {marker!r}): "
            "use a Skills-only endpoint/audience"
        )


def is_loopback_host(hostname: Optional[str]) -> bool:
    if not hostname:
        return False
    host = hostname.strip().lower().strip("[]")
    return host in {"127.0.0.1", "localhost", "::1"}


def require_https_outside_local_test(
    url: str,
    *,
    auth_mode: str,
    label: str,
) -> str:
    """Enforce https for PACI/Gateway URLs outside local-test loopback.

    Coordinated gate (L1/L2): ``LINKSKILLS_AUTH_MODE=local-test`` plus a
    loopback host may use http; all other modes require https.
    """
    value = url.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PaciConfigError(f"{label} must be an absolute http(s) URI")
    if parsed.scheme == "https":
        return value
    if auth_mode == AUTH_MODE_LOCAL_TEST and is_loopback_host(parsed.hostname):
        return value
    raise PaciConfigError(
        f"{label} must be https outside LINKSKILLS_AUTH_MODE=local-test "
        f"loopback (got scheme={parsed.scheme!r})"
    )


def _validate_token_endpoint(
    token_endpoint: str,
    *,
    auth_mode: str = AUTH_MODE_PRODUCTION,
) -> str:
    endpoint = token_endpoint.strip()
    _assert_skills_pinned("token_endpoint", endpoint)
    return require_https_outside_local_test(
        endpoint,
        auth_mode=auth_mode,
        label="token_endpoint",
    )


@dataclass(frozen=True)
class PaciClientConfig:
    """Skills-only PACI client configuration (no private key material)."""

    client_id: str
    token_endpoint: str
    private_key_file: Optional[Path] = None
    kid: Optional[str] = None
    scope: Optional[str] = None
    resource_audience: Optional[str] = None
    assertion_lifetime_s: int = ASSERTION_LIFETIME_MAX_S
    expected_access_ttl_s: int = EXPECTED_ACCESS_TTL_S
    early_renewal_fraction: float = EARLY_RENEWAL_FRACTION
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_base_s: float = DEFAULT_BACKOFF_BASE_S
    timeout_s: float = DEFAULT_TIMEOUT_S
    domain: str = "skills"
    auth_mode: str = AUTH_MODE_PRODUCTION
    private_key_fd: Optional[int] = None

    def __post_init__(self) -> None:
        if self.domain != "skills":
            refuse_brain_openclaw_reuse(purpose=f"PaciClientConfig(domain={self.domain!r})")
        if not self.client_id.strip():
            raise PaciConfigError("client_id is required")
        mode = str(self.auth_mode or AUTH_MODE_PRODUCTION).strip().lower()
        if mode not in {AUTH_MODE_PRODUCTION, AUTH_MODE_LOCAL_TEST}:
            raise PaciConfigError(
                f"Unknown auth_mode={self.auth_mode!r}; expected "
                f"'{AUTH_MODE_PRODUCTION}' or '{AUTH_MODE_LOCAL_TEST}'"
            )
        object.__setattr__(self, "auth_mode", mode)
        object.__setattr__(
            self,
            "token_endpoint",
            _validate_token_endpoint(self.token_endpoint, auth_mode=mode),
        )
        if self.resource_audience is not None:
            _assert_skills_pinned("resource_audience", self.resource_audience)
        if self.assertion_lifetime_s < 1 or self.assertion_lifetime_s > ASSERTION_LIFETIME_MAX_S:
            raise PaciConfigError(
                f"assertion_lifetime_s must be 1..{ASSERTION_LIFETIME_MAX_S} (contract §6.2)"
            )
        if self.expected_access_ttl_s < 1 or self.expected_access_ttl_s > MAX_ACCESS_TTL_S:
            raise PaciConfigError(
                f"expected_access_ttl_s must be 1..{MAX_ACCESS_TTL_S} "
                "(frozen access-token lifetime cap)"
            )
        if self.early_renewal_fraction <= 0 or self.early_renewal_fraction >= 1:
            raise PaciConfigError("early_renewal_fraction must be in (0, 1)")
        if (self.private_key_file is None) == (self.private_key_fd is None):
            raise PaciConfigError(
                "configure exactly one PACI private-key source: "
                f"{ENV_PRIVATE_KEY_FILE} or {ENV_PRIVATE_KEY_FD}"
            )
        if self.private_key_file is not None:
            key_path = Path(self.private_key_file)
            if not key_path.is_file():
                raise PaciConfigError(
                    "private_key_file SecretRef path does not exist or is not a file "
                    f"(set {ENV_PRIVATE_KEY_FILE})"
                )
            object.__setattr__(self, "private_key_file", key_path)
        if self.private_key_fd is not None:
            if (
                isinstance(self.private_key_fd, bool)
                or not isinstance(self.private_key_fd, int)
                or self.private_key_fd < 3
            ):
                raise PaciConfigError(
                    f"{ENV_PRIVATE_KEY_FD} must identify an inherited descriptor >= 3"
                )
            try:
                os.fstat(self.private_key_fd)
            except OSError as exc:
                raise PaciConfigError(
                    f"{ENV_PRIVATE_KEY_FD} does not identify an open inherited descriptor"
                ) from exc


@dataclass
class _CachedAccessToken:
    access_token: str
    token_type: str
    issued_at: float
    expires_at: float
    expires_in: int


@dataclass
class PaciTokenClient:
    """Obtain Skills Gateway bearers via PACI client_credentials + private_key_jwt."""

    config: PaciClientConfig
    _private_key: ec.EllipticCurvePrivateKey = field(repr=False, init=False)
    _cached: Optional[_CachedAccessToken] = field(default=None, init=False, repr=False)
    _used_assertion_jtis: Dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _urlopen: Any = field(default=urlopen, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.config.private_key_fd is not None:
            self._private_key = self._load_private_key_fd(self.config.private_key_fd)
        else:
            assert self.config.private_key_file is not None
            self._private_key = self._load_private_key_file(self.config.private_key_file)

    @staticmethod
    def _parse_private_key(raw: bytes, *, source: str) -> ec.EllipticCurvePrivateKey:
        if len(raw) >= MAX_PRIVATE_KEY_BYTES:
            raise PaciConfigError(f"PACI client private key {source} exceeds 64 KiB")
        try:
            key = serialization.load_pem_private_key(raw, password=None)
        except Exception as exc:  # noqa: BLE001 — fail closed, no key detail
            raise PaciConfigError(
                f"PACI client private key {source} is not a usable PEM private key"
            ) from exc
        if not isinstance(key, ec.EllipticCurvePrivateKey):
            raise PaciConfigError("PACI client private key must be an EC key (ES256 / P-256)")
        if not isinstance(key.curve, ec.SECP256R1):
            raise PaciConfigError("PACI client private key curve must be P-256 (SECP256R1)")
        return key

    @classmethod
    def _load_private_key_file(cls, path: Path) -> ec.EllipticCurvePrivateKey:
        # Never log path contents or key bytes.
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise PaciConfigError("unable to read PACI client private key SecretRef file") from exc
        return cls._parse_private_key(raw, source="file")

    @classmethod
    def _load_private_key_fd(cls, fd: int) -> ec.EllipticCurvePrivateKey:
        # The child owns the inherited descriptor. Read it once and close it so
        # key bytes do not remain available after client initialization.
        stream = None
        try:
            stream = os.fdopen(fd, "rb", closefd=True)
            with stream:
                raw = stream.read(MAX_PRIVATE_KEY_BYTES)
        except OSError as exc:
            # fdopen owns closure once it succeeds; close the original
            # descriptor only when fdopen itself failed.
            if stream is None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            raise PaciConfigError(
                "unable to read PACI client private key inherited descriptor"
            ) from exc
        return cls._parse_private_key(raw, source="inherited descriptor")

    @classmethod
    def from_env(
        cls,
        environ: Optional[Mapping[str, str]] = None,
        *,
        urlopen_impl: Any = None,
    ) -> "PaciTokenClient":
        env = environ if environ is not None else os.environ
        client_id = str(env.get(ENV_CLIENT_ID) or "").strip()
        token_endpoint = str(env.get(ENV_TOKEN_ENDPOINT) or "").strip()
        key_file = str(env.get(ENV_PRIVATE_KEY_FILE) or "").strip()
        key_fd_raw = str(env.get(ENV_PRIVATE_KEY_FD) or "").strip()
        if not client_id or not token_endpoint or (not key_file and not key_fd_raw):
            raise PaciConfigError(
                "PACI env incomplete: require "
                f"{ENV_CLIENT_ID}, {ENV_TOKEN_ENDPOINT}, and exactly one of "
                f"{ENV_PRIVATE_KEY_FILE} or {ENV_PRIVATE_KEY_FD}"
            )
        if key_file and key_fd_raw:
            raise PaciConfigError(
                f"configure exactly one of {ENV_PRIVATE_KEY_FILE} or {ENV_PRIVATE_KEY_FD}"
            )
        key_fd: Optional[int] = None
        if key_fd_raw:
            try:
                key_fd = int(key_fd_raw, 10)
            except ValueError as exc:
                raise PaciConfigError(f"{ENV_PRIVATE_KEY_FD} must be an integer") from exc
        kid = str(env.get(ENV_KID) or "").strip() or None
        scope = str(env.get(ENV_SCOPE) or "").strip() or None
        audience = str(env.get(ENV_RESOURCE_AUDIENCE) or "").strip() or None
        mode = resolve_auth_mode(env)
        config = PaciClientConfig(
            client_id=client_id,
            token_endpoint=token_endpoint,
            private_key_file=Path(key_file) if key_file else None,
            kid=kid,
            scope=scope,
            resource_audience=audience,
            auth_mode=mode,
            private_key_fd=key_fd,
        )
        client = cls(config=config)
        if urlopen_impl is not None:
            client._urlopen = urlopen_impl
        return client

    def status(self) -> Dict[str, Any]:
        """Safe diagnostics — never includes tokens or key material."""
        cached = self._cached
        now = time.time()
        return {
            "domain": "skills",
            "client_id": self.config.client_id,
            "token_endpoint": self.config.token_endpoint,
            "resource_audience": self.config.resource_audience,
            "scope": self.config.scope,
            "kid_configured": bool(self.config.kid),
            "private_key_file_set": self.config.private_key_file is not None,
            "private_key_fd_set": self.config.private_key_fd is not None,
            "has_cached_token": cached is not None,
            "cached_expires_in_s": (
                max(0, int(cached.expires_at - now)) if cached is not None else None
            ),
            "needs_renewal": self._needs_renewal(),
            "live_proven": False,
            "note": "Skills-owned PACI client implemented locally; Platform PACI issuer absent",
        }

    def invalidate(self) -> None:
        """Drop cached access token (e.g. after resource-server HTTP 401)."""
        self._cached = None

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        """Return a usable access token, renewing early when TTL < 20% remaining."""
        if force_refresh or self._needs_renewal():
            self._mint_with_retry()
        assert self._cached is not None
        return self._cached.access_token

    def authorization_header(self, *, force_refresh: bool = False) -> str:
        token = self.get_access_token(force_refresh=force_refresh)
        return f"Bearer {token}"

    def _needs_renewal(self) -> bool:
        cached = self._cached
        if cached is None:
            return True
        now = time.time()
        if now >= cached.expires_at:
            return True
        lifetime = max(cached.expires_at - cached.issued_at, 1.0)
        remaining = cached.expires_at - now
        return remaining < (lifetime * self.config.early_renewal_fraction)

    def _purge_expired_jtis(self, now: float) -> None:
        expired = [jti for jti, exp in self._used_assertion_jtis.items() if exp <= now]
        for jti in expired:
            del self._used_assertion_jtis[jti]

    def _next_assertion_jti(self, now: float, assertion_exp: float) -> str:
        """Allocate a locally unique assertion jti (replay-safe client side)."""
        self._purge_expired_jtis(now)
        for _ in range(8):
            jti = str(uuid.uuid4())
            if jti not in self._used_assertion_jtis:
                self._used_assertion_jtis[jti] = assertion_exp
                return jti
        raise PaciTokenError("unable to allocate unique assertion jti")

    def build_client_assertion(self, *, now: Optional[float] = None) -> str:
        """Build a compact JWS client assertion (ES256). Does not mint a token."""
        issued = int(now if now is not None else time.time())
        lifetime = self.config.assertion_lifetime_s
        exp = issued + lifetime
        jti = self._next_assertion_jti(float(issued), float(exp))
        header: Dict[str, Any] = {"alg": "ES256", "typ": "JWT"}
        if self.config.kid:
            header["kid"] = self.config.kid
        claims = {
            "iss": self.config.client_id,
            "sub": self.config.client_id,
            "aud": self.config.token_endpoint,
            "iat": issued,
            "exp": exp,
            "jti": jti,
        }
        signing_input = (
            f"{_b64url(json.dumps(header, separators=(',', ':'), sort_keys=True).encode('utf-8'))}."
            f"{_b64url(json.dumps(claims, separators=(',', ':'), sort_keys=True).encode('utf-8'))}"
        ).encode("ascii")
        der_sig = self._private_key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(der_sig)
        raw_sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        return f"{signing_input.decode('ascii')}.{_b64url(raw_sig)}"

    def _mint_with_retry(self) -> None:
        attempts = max(1, self.config.max_retries + 1)
        last_error: Optional[BaseException] = None
        for attempt in range(attempts):
            try:
                self._mint_once()
                return
            except PaciAuthError:
                raise
            except PaciConfigError:
                raise
            except PaciTransientError as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                delay = self.config.backoff_base_s * (2**attempt)
                logger.warning(
                    "PACI token mint transient failure (attempt %s/%s); backing off %.2fs",
                    attempt + 1,
                    attempts,
                    delay,
                )
                time.sleep(delay)
        raise PaciTransientError(
            f"PACI token mint failed after {attempts} attempts"
        ) from last_error

    def _mint_once(self) -> None:
        assertion = self.build_client_assertion()
        form: Dict[str, str] = {
            "grant_type": "client_credentials",
            "client_assertion_type": CLIENT_ASSERTION_TYPE,
            "client_assertion": assertion,
            "client_id": self.config.client_id,
        }
        if self.config.scope:
            form["scope"] = self.config.scope
        body = urlencode(form).encode("utf-8")
        req = Request(
            self.config.token_endpoint,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )
        try:
            with self._urlopen(req, timeout=self.config.timeout_s) as response:
                status = getattr(response, "status", None) or response.getcode()
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            exc.read().decode("utf-8", errors="replace")
            if exc.code in {400, 401, 403}:
                # Fail closed — do not retry credential/assertion failures.
                raise PaciAuthError(
                    f"PACI token endpoint auth failure HTTP {exc.code}"
                ) from exc
            if exc.code >= 500 or exc.code == 429:
                raise PaciTransientError(
                    f"PACI token endpoint transient HTTP {exc.code}"
                ) from exc
            raise PaciAuthError(f"PACI token endpoint rejected mint HTTP {exc.code}") from exc
        except URLError as exc:
            raise PaciTransientError("PACI token endpoint unreachable") from exc

        if status is not None and int(status) >= 400:
            if int(status) in {400, 401, 403}:
                raise PaciAuthError(f"PACI token endpoint auth failure HTTP {status}")
            raise PaciTransientError(f"PACI token endpoint HTTP {status}")

        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise PaciAuthError("PACI token endpoint returned non-JSON body") from exc
        if not isinstance(payload, dict):
            raise PaciAuthError("PACI token endpoint JSON must be an object")

        error = payload.get("error")
        if error:
            # OAuth error responses are auth failures (fail closed).
            raise PaciAuthError(f"PACI token error: {error}")

        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            raise PaciAuthError("PACI mint response missing access_token")
        token_type = str(payload.get("token_type") or "Bearer").strip() or "Bearer"
        if token_type.lower() != "bearer":
            raise PaciAuthError(f"PACI mint returned unsupported token_type={token_type!r}")

        # Phase-1: ignore any refresh_token if a non-compliant AS returns one.
        if "refresh_token" in payload and payload.get("refresh_token"):
            logger.info(
                "PACI mint included refresh_token; Skills client ignores it (phase-1 no refresh)"
            )

        expires_in_raw = payload.get("expires_in")
        if expires_in_raw is None:
            expires_in = self.config.expected_access_ttl_s
        else:
            try:
                expires_in = int(expires_in_raw)
            except (TypeError, ValueError) as exc:
                raise PaciAuthError("PACI mint expires_in must be an integer") from exc
        if expires_in < 1:
            raise PaciAuthError("PACI mint expires_in must be positive")
        if expires_in > MAX_ACCESS_TTL_S:
            # Fail closed — never accept AS lifetime above frozen 900s cap.
            raise PaciAuthError(
                f"PACI mint expires_in={expires_in} exceeds max {MAX_ACCESS_TTL_S}s"
            )

        now = time.time()
        self._cached = _CachedAccessToken(
            access_token=access_token.strip(),
            token_type=token_type,
            issued_at=now,
            expires_at=now + float(expires_in),
            expires_in=expires_in,
        )


def paci_env_configured(environ: Optional[Mapping[str, str]] = None) -> bool:
    """True when Skills PACI auth env has a configured key source."""
    env = environ if environ is not None else os.environ
    return bool(
        str(env.get(ENV_CLIENT_ID) or "").strip()
        and str(env.get(ENV_TOKEN_ENDPOINT) or "").strip()
        and bool(
            str(env.get(ENV_PRIVATE_KEY_FILE) or "").strip()
            or str(env.get(ENV_PRIVATE_KEY_FD) or "").strip()
        )
    )


def resolve_auth_mode(environ: Optional[Mapping[str, str]] = None) -> str:
    env = environ if environ is not None else os.environ
    raw = str(env.get(ENV_AUTH_MODE) or AUTH_MODE_PRODUCTION).strip().lower()
    if raw in {AUTH_MODE_PRODUCTION, AUTH_MODE_LOCAL_TEST}:
        return raw
    raise PaciConfigError(
        f"Unknown {ENV_AUTH_MODE}={raw!r}; expected '{AUTH_MODE_PRODUCTION}' "
        f"or '{AUTH_MODE_LOCAL_TEST}'"
    )
