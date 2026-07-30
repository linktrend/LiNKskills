"""Ephemeral ES256 / PACI test helpers (evidence class: fake_local).

Does not use live Platform keys. Tokens minted here are for adversarial unit
tests only. Prefer dependency injection over real network I/O.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives import serialization

from linkskills_gateway.auth import CLAIM_CONTRACT_VERSION
from linkskills_gateway.paci_jwt import b64url_encode
from linkskills_gateway.paci_types import (
    EVIDENCE_CLASS_FAKE_LOCAL,
    MAX_ACCESS_TOKEN_TTL_SECONDS,
    PACI_ALG,
    PACI_CLAIMS_NAMESPACE,
    PACI_TOKEN_TYP,
)


def _int_to_b64url_u256(value: int) -> str:
    return b64url_encode(value.to_bytes(32, "big"))


def generate_es256_keypair() -> Tuple[ec.EllipticCurvePrivateKey, Dict[str, Any]]:
    """Return (private_key, public_jwk) with a fresh UUID kid."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_numbers = private_key.public_key().public_numbers()
    kid = str(uuid.uuid4())
    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": _int_to_b64url_u256(public_numbers.x),
        "y": _int_to_b64url_u256(public_numbers.y),
        "alg": PACI_ALG,
        "use": "sig",
        "kid": kid,
        "key_ops": ["verify"],
    }
    return private_key, jwk


def write_ec_private_key_pem(private_key: ec.EllipticCurvePrivateKey, path: str) -> None:
    """Write a PEM private key for SecretRef signer tests (never log contents)."""
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(path, "wb") as handle:
        handle.write(pem)


def epoch_to_iso(epoch: int) -> str:
    return (
        datetime.fromtimestamp(int(epoch), tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def default_auth_claims(
    *,
    issuer: str,
    audience: Sequence[str],
    actor_id: str = "actor-skills-test",
    issued_at: Optional[int] = None,
    expires_at: Optional[int] = None,
    now: Optional[float] = None,
    ttl_seconds: int = MAX_ACCESS_TOKEN_TTL_SECONDS,
    **overrides: Any,
) -> Dict[str, Any]:
    """Build a frozen AuthClaims 1.1.0 object aligned to whole-second bounds."""
    base_now = int(now if now is not None else time.time())
    iat = int(issued_at if issued_at is not None else base_now)
    exp = int(expires_at if expires_at is not None else (iat + ttl_seconds))
    claims: Dict[str, Any] = {
        "claimContractVersion": CLAIM_CONTRACT_VERSION,
        "actorId": actor_id,
        "actorKind": "service",
        "runtimeBindingId": "bind-skills-test-1",
        "credentialId": "cred-skills-test-1",
        "orgId": "org-internal",
        "internal": True,
        "serviceScopes": ["lskills", "linkplatform"],
        "permittedOperations": [
            "read",
            "execute",
            "skills:read",
            "skills:write",
            "skills:run",
            "skills:feedback",
        ],
        "issuedAt": epoch_to_iso(iat),
        "expiresAt": epoch_to_iso(exp),
        "issuer": issuer,
        "audience": list(audience),
        "correlationId": f"corr-mint-{uuid.uuid4().hex[:12]}",
    }
    claims.update(overrides)
    return claims


def sign_es256_compact(
    *,
    private_key: ec.EllipticCurvePrivateKey,
    header: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> str:
    """Mint a compact JWS with ES256 (raw R||S signature)."""
    raw_header = b64url_encode(
        json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    raw_payload = b64url_encode(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    signing_input = f"{raw_header}.{raw_payload}".encode("ascii")
    der = private_key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    raw_sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return f"{raw_header}.{raw_payload}.{b64url_encode(raw_sig)}"


def mint_paci_token(
    *,
    private_key: ec.EllipticCurvePrivateKey,
    kid: str,
    issuer: str,
    audience: Sequence[str],
    claims: Optional[Mapping[str, Any]] = None,
    now: Optional[float] = None,
    header_overrides: Optional[Mapping[str, Any]] = None,
    payload_overrides: Optional[Mapping[str, Any]] = None,
    omit_auth_claims: bool = False,
    unsigned: bool = False,
    ttl_seconds: int = MAX_ACCESS_TOKEN_TTL_SECONDS,
) -> str:
    """Mint a PACI access token (fake_local) with AuthClaims embedding."""
    base_now = int(now if now is not None else time.time())
    auth_claims = dict(
        claims
        or default_auth_claims(
            issuer=issuer,
            audience=audience,
            now=base_now,
            ttl_seconds=ttl_seconds,
        )
    )
    # Align registered claims to AuthClaims second boundaries.
    from linkskills_gateway.paci_jwt import _iso_to_epoch_seconds

    iat = _iso_to_epoch_seconds(auth_claims["issuedAt"])
    exp = _iso_to_epoch_seconds(auth_claims["expiresAt"])
    header: Dict[str, Any] = {
        "typ": PACI_TOKEN_TYP,
        "alg": PACI_ALG,
        "kid": kid,
    }
    if header_overrides:
        header.update(dict(header_overrides))

    payload: Dict[str, Any] = {
        "iss": issuer,
        "aud": list(audience),
        "sub": str(auth_claims["actorId"]),
        "iat": iat,
        "nbf": iat,
        "exp": exp,
        "jti": str(uuid.uuid4()),
    }
    if not omit_auth_claims:
        payload[PACI_CLAIMS_NAMESPACE] = auth_claims
    if payload_overrides:
        payload.update(dict(payload_overrides))

    if unsigned:
        # alg=none style: empty signature segment (still rejected by verifier).
        raw_header = b64url_encode(
            json.dumps(header, separators=(",", ":")).encode("utf-8")
        )
        raw_payload = b64url_encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        )
        return f"{raw_header}.{raw_payload}."

    return sign_es256_compact(
        private_key=private_key, header=header, payload=payload
    )


class InMemoryJwksStore:
    """Mutable in-memory JWKS document for injection into CachedJwksClient."""

    evidence_class = EVIDENCE_CLASS_FAKE_LOCAL

    def __init__(self, keys: Optional[Sequence[Mapping[str, Any]]] = None) -> None:
        self._keys: Dict[str, Dict[str, Any]] = {}
        for key in keys or ():
            self.add_key(key)

    def add_key(self, jwk: Mapping[str, Any]) -> None:
        kid = str(jwk["kid"])
        self._keys[kid] = dict(jwk)

    def remove_kid(self, kid: str) -> None:
        self._keys.pop(str(kid), None)

    def document(self) -> Dict[str, List[Dict[str, Any]]]:
        return {"keys": list(self._keys.values())}

    def fetch_bytes(self, _url: str) -> bytes:
        return json.dumps(self.document()).encode("utf-8")


class FakeIntrospectionBackend:
    """Injectable introspection HTTP backend for unit tests."""

    def __init__(self) -> None:
        self.status: int = 200
        self.body: MutableMapping[str, Any] = {"active": True}
        self.down: bool = False
        self.calls: List[Dict[str, Any]] = []
        self.timeout: bool = False

    def set_active(
        self,
        *,
        jti: str,
        iss: str,
        sub: str,
        aud: Optional[Sequence[str]] = None,
        client_id: str = "skills-gateway",
        credential_id: str = "cred-skills-test-1",
        runtime_binding_id: str = "bind-skills-test-1",
        iat: Optional[int] = None,
        exp: Optional[int] = None,
        scope: str = "lskills",
        token_type: str = "Bearer",
        omit_fields: Optional[Sequence[str]] = None,
    ) -> None:
        self.status = 200
        self.down = False
        self.timeout = False
        now = int(time.time())
        self.body = {
            "active": True,
            "iss": iss,
            "aud": list(aud or ["lskills-api"]),
            "sub": sub,
            "exp": int(exp if exp is not None else now + 900),
            "iat": int(iat if iat is not None else now),
            "jti": jti,
            "client_id": client_id,
            "scope": scope,
            "credential_id": credential_id,
            "runtime_binding_id": runtime_binding_id,
            "token_type": token_type,
        }
        for field in omit_fields or ():
            self.body.pop(str(field), None)

    def set_inactive(self) -> None:
        """Privacy: inactive responses expose only active:false."""
        self.status = 200
        self.down = False
        self.timeout = False
        self.body = {"active": False}

    def set_unauthorized(self) -> None:
        self.status = 401
        self.down = False
        self.timeout = False
        self.body = {"error": "invalid_client"}

    def set_down(self) -> None:
        self.down = True
        self.timeout = False

    def set_timeout(self) -> None:
        self.timeout = True
        self.down = False

    def fetch(
        self, url: str, headers: Mapping[str, str], body: bytes
    ) -> tuple[int, bytes]:
        self.calls.append({"url": url, "headers": dict(headers), "body": body})
        if self.timeout:
            raise TimeoutError("introspection endpoint timeout (fake)")
        if self.down:
            raise ConnectionError("introspection endpoint down (fake)")
        return self.status, json.dumps(self.body).encode("utf-8")
