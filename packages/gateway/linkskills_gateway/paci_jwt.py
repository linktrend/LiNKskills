"""PACI compact JWS (ES256) verification and AuthClaims extraction.

**Evidence class:** implemented but not proven against frozen Platform PACI
service (envelope ``platform.auth-token-envelope/0.1.3-draft``).

Uses ``cryptography`` for ES256 — no PyJWT/jose dependency.
"""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Set

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from .auth import AuthError, CLAIM_CONTRACT_VERSION
from .jwks import JwksKeyProvider
from .paci_types import (
    AUTH_CLAIMS_CONTRACT_VERSION,
    CLOCK_SKEW_SECONDS,
    FORBIDDEN_ALGS,
    FORBIDDEN_HEADER_KEY_PARAMS,
    PACI_ALG,
    PACI_CLAIMS_NAMESPACE,
    PACI_TOKEN_TYP,
    UNDERSTOOD_CRIT_HEADERS,
)


def b64url_decode(data: str) -> bytes:
    """Decode base64url without requiring padding."""
    text = data.strip()
    pad = "=" * (-len(text) % 4)
    try:
        return base64.urlsafe_b64decode(text + pad)
    except Exception as exc:  # noqa: BLE001
        raise AuthError("auth_malformed", "Invalid base64url segment") from exc


def b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _parse_json_object(raw: bytes, *, label: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthError("auth_malformed", f"Invalid JSON in JWT {label}") from exc
    if not isinstance(data, dict):
        raise AuthError("auth_malformed", f"JWT {label} must be a JSON object")
    return data


@dataclass(frozen=True)
class ParsedCompactJws:
    """Split compact JWS parts (unverified)."""

    header: Mapping[str, Any]
    payload: Mapping[str, Any]
    signing_input: bytes
    signature: bytes
    raw_header: str
    raw_payload: str
    raw_token: str


def parse_compact_jws(token: str) -> ParsedCompactJws:
    """Parse JWS compact serialization; reject malformed structure."""
    text = str(token).strip()
    if not text or text.count(".") != 2:
        raise AuthError(
            "auth_malformed",
            "PACI token must be compact JWS with exactly three segments",
        )
    if text.startswith("platform.") or text.startswith("fake.") or text.startswith("{"):
        raise AuthError(
            "auth_unsigned_rejected",
            "Unsigned / non-PACI token formats are rejected by PACI verifier",
        )
    raw_header, raw_payload, raw_sig = text.split(".")
    if not raw_header or not raw_payload or not raw_sig:
        raise AuthError("auth_malformed", "PACI compact JWS segments must be non-empty")
    header = _parse_json_object(b64url_decode(raw_header), label="header")
    payload = _parse_json_object(b64url_decode(raw_payload), label="payload")
    signature = b64url_decode(raw_sig)
    signing_input = f"{raw_header}.{raw_payload}".encode("ascii")
    return ParsedCompactJws(
        header=header,
        payload=payload,
        signing_input=signing_input,
        signature=signature,
        raw_header=raw_header,
        raw_payload=raw_payload,
        raw_token=text,
    )


def validate_paci_header(header: Mapping[str, Any]) -> str:
    """Require typ/alg/kid; reject forbidden algs and key-selection headers.

    Returns the ``kid`` string.
    """
    # Duplicate / ambiguous headers cannot appear in a JSON object after parse;
    # still reject explicit nulls for required fields.
    typ = header.get("typ")
    if typ != PACI_TOKEN_TYP:
        raise AuthError(
            "auth_invalid",
            f"JWT typ must be {PACI_TOKEN_TYP!r}, got {typ!r}",
        )
    alg = header.get("alg")
    alg_text = str(alg) if alg is not None else ""
    if alg_text in FORBIDDEN_ALGS or alg_text.upper().startswith("HS"):
        raise AuthError(
            "auth_alg_rejected",
            f"Forbidden JWT alg {alg_text!r} (algorithm confusion hardening)",
        )
    if alg_text != PACI_ALG:
        raise AuthError(
            "auth_alg_rejected",
            f"JWT alg must be {PACI_ALG!r}, got {alg_text!r}",
        )
    for forbidden in FORBIDDEN_HEADER_KEY_PARAMS:
        if forbidden in header:
            raise AuthError(
                "auth_header_rejected",
                f"Forbidden JWT header parameter {forbidden!r} for key selection",
            )
    crit = header.get("crit")
    if crit is not None:
        if not isinstance(crit, list) or not crit:
            raise AuthError("auth_invalid", "JWT crit must be a non-empty array")
        for name in crit:
            key = str(name)
            if key not in UNDERSTOOD_CRIT_HEADERS:
                raise AuthError(
                    "auth_invalid",
                    f"JWT crit lists unknown header {key!r}",
                )
            if key not in header:
                raise AuthError(
                    "auth_invalid",
                    f"JWT crit header {key!r} missing from protected header",
                )
    kid = str(header.get("kid") or "").strip()
    if not kid:
        raise AuthError("auth_invalid", "JWT header kid is required")
    return kid


def jwk_ec_p256_public_key(jwk: Mapping[str, Any]) -> ec.EllipticCurvePublicKey:
    """Build an EC P-256 public key from a JWK dict."""
    try:
        x = int.from_bytes(b64url_decode(str(jwk["x"])), "big")
        y = int.from_bytes(b64url_decode(str(jwk["y"])), "big")
    except (KeyError, AuthError, ValueError) as exc:
        raise AuthError("jwks_invalid", "EC JWK missing/invalid x/y") from exc
    numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1())
    try:
        return numbers.public_key()
    except ValueError as exc:
        raise AuthError("jwks_invalid", "EC JWK point is not on P-256") from exc


def _raw_es256_signature_to_der(signature: bytes) -> bytes:
    """Convert JWS R||S (64 bytes) to DER for cryptography verify."""
    if len(signature) != 64:
        raise AuthError(
            "auth_invalid",
            f"ES256 signature must be 64 raw bytes, got {len(signature)}",
        )
    r = int.from_bytes(signature[:32], "big")
    s = int.from_bytes(signature[32:], "big")
    return encode_dss_signature(r, s)


def verify_es256_signature(
    *,
    signing_input: bytes,
    signature: bytes,
    public_key: ec.EllipticCurvePublicKey,
) -> None:
    """Verify ES256 (ECDSA P-256 + SHA-256) over the JWS signing input."""
    try:
        der = _raw_es256_signature_to_der(signature)
        public_key.verify(der, signing_input, ec.ECDSA(hashes.SHA256()))
    except AuthError:
        raise
    except InvalidSignature as exc:
        raise AuthError("auth_signature_invalid", "ES256 signature verification failed") from exc
    except Exception as exc:  # noqa: BLE001
        raise AuthError("auth_signature_invalid", f"ES256 verify error: {exc}") from exc


def _as_string_set(value: Any, *, field: str) -> Set[str]:
    if isinstance(value, str):
        # JWT aud may be a single string per RFC 7519; treat as singleton set.
        text = value.strip()
        if not text:
            raise AuthError("auth_invalid", f"{field} must be non-empty")
        return {text}
    if not isinstance(value, list) or not value:
        raise AuthError("auth_invalid", f"{field} must be a non-empty array (or string)")
    out = {str(item).strip() for item in value}
    if "" in out or len(out) != len(value):
        # Reject empty entries; allow set semantics for equality later.
        if "" in out:
            raise AuthError("auth_invalid", f"{field} entries must be non-empty")
    return out


def _require_numeric_date(payload: Mapping[str, Any], name: str) -> int:
    value = payload.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AuthError("auth_invalid", f"JWT claim {name} must be NumericDate (number)")
    return int(value)


def validate_registered_claims(
    payload: Mapping[str, Any],
    *,
    expected_issuer: str,
    expected_audiences: Sequence[str],
    now: Optional[float] = None,
    skew_seconds: int = CLOCK_SKEW_SECONDS,
) -> Dict[str, Any]:
    """Validate iss/aud/sub/iat/exp/nbf/jti with zero skew (default)."""
    if skew_seconds != 0:
        raise AuthError(
            "auth_config",
            "PACI Phase-1 clock skew must be 0 (AuthClaims contract)",
        )
    iss = str(payload.get("iss") or "").strip()
    if not iss:
        raise AuthError("auth_invalid", "JWT iss is required")
    if iss != expected_issuer:
        raise AuthError(
            "auth_forbidden",
            f"Wrong issuer: expected {expected_issuer!r}, got {iss!r}",
        )
    sub = str(payload.get("sub") or "").strip()
    if not sub:
        raise AuthError("auth_invalid", "JWT sub is required")
    aud = _as_string_set(payload.get("aud"), field="aud")
    expected = {str(a).strip() for a in expected_audiences if str(a).strip()}
    if not expected:
        raise AuthError("auth_config", "expected audiences must be non-empty")
    if aud != expected:
        raise AuthError(
            "auth_forbidden",
            f"Wrong audience set: expected {sorted(expected)}, got {sorted(aud)}",
        )
    iat = _require_numeric_date(payload, "iat")
    exp = _require_numeric_date(payload, "exp")
    nbf = _require_numeric_date(payload, "nbf")
    jti = str(payload.get("jti") or "").strip()
    if not jti:
        raise AuthError("auth_invalid", "JWT jti is required")

    now_epoch = int(time.time() if now is None else now)
    # Zero skew: reject if now < nbf/iat; reject if now >= exp.
    if now_epoch < nbf:
        raise AuthError("auth_not_yet_valid", "JWT nbf not yet valid")
    if now_epoch < iat:
        raise AuthError("auth_not_yet_valid", "JWT iat not yet valid")
    if now_epoch >= exp:
        raise AuthError("auth_expired", "JWT expired")
    if nbf != iat:
        # Phase-1 mint rule: nbf === iat
        raise AuthError("auth_invalid", "Phase-1 PACI requires nbf == iat")
    if exp <= iat:
        raise AuthError("auth_invalid", "JWT exp must be greater than iat")

    return {
        "iss": iss,
        "sub": sub,
        "aud": frozenset(aud),
        "iat": iat,
        "exp": exp,
        "nbf": nbf,
        "jti": jti,
    }


def _iso_to_epoch_seconds(value: Any) -> int:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise AuthError("auth_invalid", f"AuthClaims time not ISO-8601: {value!r}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def extract_auth_claims(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Extract the namespaced AuthClaims object; forbid extra payload props."""
    allowed_top = {
        "iss",
        "aud",
        "sub",
        "iat",
        "exp",
        "nbf",
        "jti",
        PACI_CLAIMS_NAMESPACE,
    }
    extra = sorted(set(payload.keys()) - allowed_top)
    if extra:
        raise AuthError(
            "auth_invalid",
            "PACI payload has forbidden extra properties: " + ", ".join(extra),
        )
    claims = payload.get(PACI_CLAIMS_NAMESPACE)
    if not isinstance(claims, dict):
        raise AuthError(
            "auth_invalid",
            f"PACI payload missing AuthClaims at {PACI_CLAIMS_NAMESPACE!r}",
        )
    return dict(claims)


def assert_cross_field_equality(
    payload: Mapping[str, Any],
    claims: Mapping[str, Any],
    *,
    registered: Mapping[str, Any],
) -> None:
    """Enforce envelope §4.1 cross-field equality with AuthClaims."""
    version = str(claims.get("claimContractVersion") or "").strip()
    if version != AUTH_CLAIMS_CONTRACT_VERSION and version != CLAIM_CONTRACT_VERSION:
        raise AuthError(
            "auth_contract_mismatch",
            f"claimContractVersion must be {AUTH_CLAIMS_CONTRACT_VERSION!r}, "
            f"got {version!r}",
        )
    issuer = str(claims.get("issuer") or "").strip()
    if registered["iss"] != issuer:
        raise AuthError(
            "auth_invalid",
            f"payload.iss !== claims.issuer ({registered['iss']!r} vs {issuer!r})",
        )
    actor_id = str(claims.get("actorId") or "").strip()
    if registered["sub"] != actor_id:
        raise AuthError(
            "auth_invalid",
            f"payload.sub !== claims.actorId ({registered['sub']!r} vs {actor_id!r})",
        )
    claims_aud = claims.get("audience")
    if not isinstance(claims_aud, list):
        raise AuthError("auth_invalid", "AuthClaims audience must be an array")
    claims_aud_set = {str(x).strip() for x in claims_aud}
    if claims_aud_set != set(registered["aud"]):
        raise AuthError(
            "auth_invalid",
            "payload.aud set-inequal to claims.audience",
        )
    issued = _iso_to_epoch_seconds(claims.get("issuedAt"))
    expires = _iso_to_epoch_seconds(claims.get("expiresAt"))
    if issued != registered["iat"] or issued != registered["nbf"]:
        raise AuthError(
            "auth_invalid",
            "AuthClaims issuedAt second boundary must equal JWT iat/nbf",
        )
    if expires != registered["exp"]:
        raise AuthError(
            "auth_invalid",
            "AuthClaims expiresAt second boundary must equal JWT exp",
        )


@dataclass(frozen=True)
class VerifiedPaciToken:
    """Result of PACI JWT cryptographic + claim validation."""

    claims: Mapping[str, Any]
    jti: str
    kid: str
    iss: str
    sub: str
    aud: frozenset[str]
    iat: int
    exp: int
    nbf: int
    raw_token: str


class PaciJwtVerifier:
    """Verify PACI compact JWS and return frozen AuthClaims payload."""

    def __init__(
        self,
        *,
        issuer: str,
        audiences: Sequence[str],
        jwks: JwksKeyProvider,
        now_fn: Optional[Callable[[], float]] = None,
    ) -> None:
        self.issuer = str(issuer).strip()
        self.audiences = [str(a).strip() for a in audiences if str(a).strip()]
        if not self.issuer:
            raise AuthError("auth_config", "PACI issuer is required")
        if not self.audiences:
            raise AuthError("auth_config", "PACI audiences are required")
        self.jwks = jwks
        self._now = now_fn or time.time

    def verify(self, token: str) -> VerifiedPaciToken:
        parsed = parse_compact_jws(token)
        kid = validate_paci_header(parsed.header)
        jwk = self.jwks.get_key(kid)
        public_key = jwk_ec_p256_public_key(jwk)
        verify_es256_signature(
            signing_input=parsed.signing_input,
            signature=parsed.signature,
            public_key=public_key,
        )
        registered = validate_registered_claims(
            parsed.payload,
            expected_issuer=self.issuer,
            expected_audiences=self.audiences,
            now=self._now(),
            skew_seconds=CLOCK_SKEW_SECONDS,
        )
        claims = extract_auth_claims(parsed.payload)
        assert_cross_field_equality(parsed.payload, claims, registered=registered)
        return VerifiedPaciToken(
            claims=claims,
            jti=str(registered["jti"]),
            kid=kid,
            iss=str(registered["iss"]),
            sub=str(registered["sub"]),
            aud=frozenset(registered["aud"]),
            iat=int(registered["iat"]),
            exp=int(registered["exp"]),
            nbf=int(registered["nbf"]),
            raw_token=parsed.raw_token,
        )
