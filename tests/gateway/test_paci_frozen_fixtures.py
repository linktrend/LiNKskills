"""Frozen Platform PACI envelope fixtures + signed TTL cases (Lane L1).

Pins:
  platform.auth-token-envelope/0.1.0
  @linktrend/platform-contracts@0.3.0
  schema bytes SHA-256 7173b9f9…463eed
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from typing import Any, Dict

from linkskills_gateway.auth import AuthError
from linkskills_gateway.jwks import StaticJwksProvider
from linkskills_gateway.paci_jwt import (
    PaciJwtVerifier,
    validate_envelope_payload_shape,
)
from linkskills_gateway.paci_types import (
    MAX_ACCESS_TOKEN_TTL_SECONDS,
    PACI_ENVELOPE_CONTENT_HASH,
    PACI_ENVELOPE_CONTRACT,
    PACI_ENVELOPE_SCHEMA_BYTES_SHA256,
    PLATFORM_CONTRACTS_PACKAGE_PACI,
    PLATFORM_HEAD_PACI,
)

from tests.gateway.paci_fakes import (
    default_auth_claims,
    generate_es256_keypair,
    mint_paci_token,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT
    / "packages"
    / "contracts"
    / "schemas"
    / "platform-auth-token-envelope.v0.1.0.json"
)
FIXTURES_DIR = (
    REPO_ROOT / "packages" / "contracts" / "fixtures" / "auth-token-envelope"
)

ISSUER = "https://auth.stage.linkplatform.linktrend.dev"
AUDIENCE = ["lskills-api"]


def _load_fixture(name: str) -> Dict[str, Any]:
    path = FIXTURES_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class PaciFrozenFixtureTests(unittest.TestCase):
    def test_pins_and_schema_bytes_hash(self) -> None:
        self.assertEqual(PACI_ENVELOPE_CONTRACT, "platform.auth-token-envelope/0.1.0")
        self.assertEqual(PLATFORM_CONTRACTS_PACKAGE_PACI, "0.3.0")
        self.assertEqual(
            PLATFORM_HEAD_PACI, "0455846487d0b8c583859060ba8b4be70e7f0b48"
        )
        self.assertEqual(MAX_ACCESS_TOKEN_TTL_SECONDS, 900)
        raw = SCHEMA_PATH.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual(digest, PACI_ENVELOPE_SCHEMA_BYTES_SHA256)
        # contentHash is Platform canonicalizeJson+sha256; pin string must be present.
        self.assertEqual(
            PACI_ENVELOPE_CONTENT_HASH,
            "9335b1855c3b3a5ec01b40c18ea85a98826192cbfba3110e07399d896e890a12",
        )

    def test_accept_valid_fixture(self) -> None:
        fixture = _load_fixture("accept-valid.json")
        self.assertEqual(fixture["expect"], "accept")
        result = validate_envelope_payload_shape(fixture["payload"])
        self.assertEqual(result["registered"]["exp"] - result["registered"]["iat"], 900)

    def test_accept_token_reuse_correlation_fixture(self) -> None:
        fixture = _load_fixture("accept-token-reuse-correlation.json")
        self.assertEqual(fixture["expect"], "accept")
        result = validate_envelope_payload_shape(fixture["payload"])
        self.assertEqual(
            result["claims"]["correlationId"],
            fixture["expectations"]["mintCorrelationIdConstant"],
        )
        # Access-token jti multi-use allowed (fixture expectation).
        self.assertFalse(fixture["expectations"]["accessTokenJtiReplayRejected"])

    def test_reject_extra_payload_field_fixture(self) -> None:
        fixture = _load_fixture("reject-extra-payload-field.json")
        with self.assertRaises(AuthError) as ctx:
            validate_envelope_payload_shape(fixture["payload"])
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_reject_cross_field_iss_fixture(self) -> None:
        fixture = _load_fixture("reject-cross-field-iss.json")
        with self.assertRaises(AuthError) as ctx:
            validate_envelope_payload_shape(fixture["payload"])
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_reject_nbf_not_iat_fixture(self) -> None:
        fixture = _load_fixture("reject-nbf-not-iat.json")
        with self.assertRaises(AuthError) as ctx:
            validate_envelope_payload_shape(fixture["payload"])
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_reject_issuer_trailing_slash_fixture(self) -> None:
        fixture = _load_fixture("reject-issuer-trailing-slash.json")
        with self.assertRaises(AuthError) as ctx:
            validate_envelope_payload_shape(fixture["payload"])
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_metadata_discovery_fixture(self) -> None:
        fixture = _load_fixture("metadata-discovery-valid.json")
        self.assertEqual(fixture["expect"], "accept")
        meta = fixture["metadata"]
        self.assertEqual(meta["issuer"], fixture["issuer"])
        self.assertNotIn("authorization_endpoint", meta)
        self.assertEqual(meta["response_types_supported"], [])
        self.assertEqual(
            meta["token_endpoint_auth_methods_supported"], ["private_key_jwt"]
        )
        self.assertTrue(meta["token_endpoint"].startswith("https://"))
        self.assertTrue(meta["jwks_uri"].startswith("https://"))
        self.assertTrue(meta["introspection_endpoint"].startswith("https://"))
        expected_discovery = fixture["issuer"] + "/.well-known/oauth-authorization-server"
        self.assertEqual(fixture["discoveryUrl"], expected_discovery)

    def test_signed_900_accepted_3600_rejected(self) -> None:
        now = 1_800_000_000.0
        private_key, jwk = generate_es256_keypair()
        jwks = StaticJwksProvider({"keys": [jwk]})
        verifier = PaciJwtVerifier(
            issuer=ISSUER,
            audiences=AUDIENCE,
            jwks=jwks,
            now_fn=lambda: now,
        )
        ok = mint_paci_token(
            private_key=private_key,
            kid=str(jwk["kid"]),
            issuer=ISSUER,
            audience=AUDIENCE,
            now=now,
            ttl_seconds=900,
        )
        verified = verifier.verify(ok)
        self.assertEqual(verified.exp - verified.iat, 900)

        long_claims = default_auth_claims(
            issuer=ISSUER,
            audience=AUDIENCE,
            now=now,
            ttl_seconds=3600,
        )
        long_token = mint_paci_token(
            private_key=private_key,
            kid=str(jwk["kid"]),
            issuer=ISSUER,
            audience=AUDIENCE,
            now=now,
            claims=long_claims,
        )
        with self.assertRaises(AuthError) as ctx:
            verifier.verify(long_token)
        self.assertEqual(ctx.exception.code, "auth_ttl_rejected")


if __name__ == "__main__":
    unittest.main()
