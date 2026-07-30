"""Adversarial PACI JWT / JWKS / introspection tests (fake_local).

Evidence: local/fake conformance against frozen
platform.auth-token-envelope/0.1.0 (@linktrend/platform-contracts@0.3.0).
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
import uuid
from typing import Any

from cryptography.hazmat.primitives import hashes, hmac as crypto_hmac

from linkskills_gateway.auth import (
    AuthConfigurationError,
    AuthError,
    HIGH_RISK_WRITE_OPERATIONS,
    PlatformClaimsVerifier,
)
from linkskills_gateway.introspection import (
    IntrospectionClient,
    LocalTestClientAssertionSigner,
    SecretRefClientAssertionSigner,
    StubClientAssertionSigner,
)
from linkskills_gateway.jwks import (
    CachedJwksClient,
    StaticJwksProvider,
    assert_https_transport,
    index_jwks_keys,
)
from linkskills_gateway.paci_authenticator import (
    PaciJwtAuthenticator,
    build_paci_authenticator_from_environ,
)
from linkskills_gateway.paci_jwt import (
    PaciJwtVerifier,
    b64url_encode,
    parse_compact_jws,
    validate_paci_header,
)
from linkskills_gateway.paci_types import (
    AUTH_CLAIMS_CONTRACT_VERSION,
    EVIDENCE_STATUS_NOT_PROVEN,
    MAX_ACCESS_TOKEN_TTL_SECONDS,
    PACI_CLAIMS_NAMESPACE,
    PACI_ENVELOPE_CONTRACT,
    PACI_ENVELOPE_CONTRACT_VERSION,
    PACI_TOKEN_TYP,
    PLATFORM_CONTRACTS_PACKAGE_PACI,
)

from tests.gateway.paci_fakes import (
    FakeIntrospectionBackend,
    InMemoryJwksStore,
    default_auth_claims,
    generate_es256_keypair,
    mint_paci_token,
    write_ec_private_key_pem,
)


ISSUER = "https://auth.stage.linkplatform.linktrend.dev"
JWKS_URI = f"{ISSUER}/.well-known/jwks.json"
AUDIENCE = ["lskills-api"]
INTROSPECT_URL = f"{ISSUER}/oauth/introspect"
CLIENT_ID = "skills-gateway"


class PaciAdversarialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 1_800_000_000.0  # fixed clock
        self.private_key, self.jwk = generate_es256_keypair()
        self.kid = str(self.jwk["kid"])
        self.jwks_store = InMemoryJwksStore([self.jwk])
        self.jwks = StaticJwksProvider(self.jwks_store.document())
        self.verifier = PaciJwtVerifier(
            issuer=ISSUER,
            audiences=AUDIENCE,
            jwks=self.jwks,
            now_fn=lambda: self.now,
        )
        self.introspect_backend = FakeIntrospectionBackend()
        self.introspection = IntrospectionClient(
            introspection_url=INTROSPECT_URL,
            client_id=CLIENT_ID,
            assertion_signer=LocalTestClientAssertionSigner(auth_mode="local-test"),
            fetch_fn=self.introspect_backend.fetch,
            now_fn=lambda: self.now,
            auth_mode="local-test",
            required_scopes=["lskills"],
        )
        self.authenticator = PaciJwtAuthenticator(
            issuer=ISSUER,
            audiences=AUDIENCE,
            jwks=self.jwks,
            introspection=self.introspection,
            now_fn=lambda: self.now,
            introspection_client_id=CLIENT_ID,
            auth_mode="local-test",
        )

    def _mint(self, **kwargs: Any) -> str:
        return mint_paci_token(
            private_key=self.private_key,
            kid=self.kid,
            issuer=ISSUER,
            audience=AUDIENCE,
            now=self.now,
            **kwargs,
        )

    def _prime_active(self, verified: Any) -> None:
        self.introspect_backend.set_active(
            jti=verified.jti,
            iss=ISSUER,
            sub=verified.sub,
            aud=sorted(verified.aud),
            client_id=CLIENT_ID,
            credential_id=str(verified.claims.get("credentialId")),
            runtime_binding_id=str(verified.claims.get("runtimeBindingId")),
            iat=verified.iat,
            exp=verified.exp,
            scope="lskills",
        )

    def test_envelope_pin_frozen_0_1_0(self) -> None:
        self.assertEqual(PACI_ENVELOPE_CONTRACT_VERSION, "0.1.0")
        self.assertEqual(PACI_ENVELOPE_CONTRACT, "platform.auth-token-envelope/0.1.0")
        self.assertEqual(PLATFORM_CONTRACTS_PACKAGE_PACI, "0.3.0")
        self.assertEqual(MAX_ACCESS_TOKEN_TTL_SECONDS, 900)

    def test_valid_paci_token_authenticates(self) -> None:
        token = self._mint()
        result = self.authenticator.authenticate(token)
        self.assertEqual(
            result.claims["claimContractVersion"], AUTH_CLAIMS_CONTRACT_VERSION
        )
        self.assertEqual(self.authenticator.evidence_status, EVIDENCE_STATUS_NOT_PROVEN)
        self.assertEqual(self.authenticator.envelope_contract, PACI_ENVELOPE_CONTRACT)

    def test_platform_claims_verifier_accepts_paci_authenticator(self) -> None:
        token = self._mint()
        verifier = PlatformClaimsVerifier(
            authenticator=self.authenticator,
            now_fn=lambda: self.now,
            expected_issuer=ISSUER,
            expected_audience="lskills-api",
        )
        claims = verifier.verify(f"Bearer {token}", now=self.now)
        self.assertEqual(claims.actor_id, "actor-skills-test")

    def test_unsigned_token_rejected(self) -> None:
        token = self._mint(unsigned=True)
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertIn(
            ctx.exception.code,
            {
                "auth_alg_rejected",
                "auth_signature_invalid",
                "auth_invalid",
                "auth_malformed",
            },
        )

    def test_alg_none_rejected(self) -> None:
        claims = default_auth_claims(issuer=ISSUER, audience=AUDIENCE, now=self.now)
        iat = int(self.now)
        header = {"typ": PACI_TOKEN_TYP, "alg": "none", "kid": self.kid}
        payload = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": claims["actorId"],
            "iat": iat,
            "nbf": iat,
            "exp": iat + 900,
            "jti": str(uuid.uuid4()),
            PACI_CLAIMS_NAMESPACE: claims,
        }
        raw_header = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
        raw_payload = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        token = f"{raw_header}.{raw_payload}.{b64url_encode(b'x' * 64)}"
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_alg_rejected")

    def test_alg_hs256_confusion_rejected(self) -> None:
        claims = default_auth_claims(issuer=ISSUER, audience=AUDIENCE, now=self.now)
        iat = int(self.now)
        header = {"typ": PACI_TOKEN_TYP, "alg": "HS256", "kid": self.kid}
        payload = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": claims["actorId"],
            "iat": iat,
            "nbf": iat,
            "exp": iat + 900,
            "jti": str(uuid.uuid4()),
            PACI_CLAIMS_NAMESPACE: claims,
        }
        raw_header = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
        raw_payload = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{raw_header}.{raw_payload}".encode("ascii")
        h = crypto_hmac.HMAC(b"not-a-platform-secret", hashes.SHA256())
        h.update(signing_input)
        mac = h.finalize()
        token = f"{raw_header}.{raw_payload}.{b64url_encode(mac)}"
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_alg_rejected")

    def test_forbidden_header_jku_rejected(self) -> None:
        token = self._mint(
            header_overrides={"jku": "https://evil.example/.well-known/jwks.json"}
        )
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_header_rejected")

    def test_forbidden_header_jwk_rejected(self) -> None:
        token = self._mint(header_overrides={"jwk": {"kty": "EC"}})
        with self.assertRaises(AuthError) as ctx:
            validate_paci_header(parse_compact_jws(token).header)
        self.assertEqual(ctx.exception.code, "auth_header_rejected")

    def test_wrong_issuer_rejected(self) -> None:
        claims = default_auth_claims(
            issuer="https://auth.evil.example",
            audience=AUDIENCE,
            now=self.now,
        )
        token = self._mint(
            claims=claims,
            payload_overrides={"iss": "https://auth.evil.example"},
        )
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_forbidden")

    def test_wrong_audience_rejected(self) -> None:
        claims = default_auth_claims(
            issuer=ISSUER,
            audience=["lbrain-api"],
            now=self.now,
        )
        token = self._mint(
            claims=claims,
            payload_overrides={"aud": ["lbrain-api"]},
        )
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_forbidden")

    def test_string_audience_rejected(self) -> None:
        token = self._mint(payload_overrides={"aud": "lskills-api"})
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_non_uuid_jti_rejected(self) -> None:
        token = self._mint(payload_overrides={"jti": "not-a-uuid"})
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_unknown_payload_field_rejected(self) -> None:
        token = self._mint(payload_overrides={"role": "service_role"})
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_ttl_900_accepted(self) -> None:
        token = self._mint(ttl_seconds=900)
        verified = self.verifier.verify(token)
        self.assertEqual(verified.exp - verified.iat, 900)

    def test_ttl_3600_rejected(self) -> None:
        """Independently reproduced 3600-second token rejection."""
        token = self._mint(ttl_seconds=3600)
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_ttl_rejected")

    def test_wrong_sub_vs_actor_id_rejected(self) -> None:
        token = self._mint(payload_overrides={"sub": "actor-someone-else"})
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_unknown_kid_rejected(self) -> None:
        token = self._mint(header_overrides={"kid": str(uuid.uuid4())})
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "jwks_unknown_kid")

    def test_expired_token_rejected(self) -> None:
        # Lifetime still ≤900 so TTL gate does not mask expiry.
        claims = default_auth_claims(
            issuer=ISSUER,
            audience=AUDIENCE,
            issued_at=int(self.now) - 600,
            expires_at=int(self.now) - 60,
        )
        token = self._mint(claims=claims)
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_expired")

    def test_nbf_not_yet_valid_rejected(self) -> None:
        future = int(self.now) + 600
        claims = default_auth_claims(
            issuer=ISSUER,
            audience=AUDIENCE,
            issued_at=future,
            expires_at=future + 900,
        )
        token = self._mint(claims=claims)
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_not_yet_valid")

    def test_wrong_authclaims_version_rejected(self) -> None:
        claims = default_auth_claims(issuer=ISSUER, audience=AUDIENCE, now=self.now)
        claims["claimContractVersion"] = "platform.auth-claims/1.0.0"
        token = self._mint(claims=claims)
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_contract_mismatch")

    def test_jwks_kid_collision_rejected(self) -> None:
        other_key, other_jwk = generate_es256_keypair()
        other_jwk["kid"] = self.kid  # collision
        with self.assertRaises(AuthError) as ctx:
            index_jwks_keys({"keys": [self.jwk, other_jwk]})
        self.assertEqual(ctx.exception.code, "jwks_kid_collision")
        _ = other_key

    def test_jwks_outage_after_cache_expiry_fail_closed(self) -> None:
        clock = {"t": self.now}

        def now_fn() -> float:
            return clock["t"]

        fetch_state = {"fail": False, "calls": 0}

        def fetch_fn(url: str) -> bytes:
            fetch_state["calls"] += 1
            if fetch_state["fail"]:
                raise AuthError("jwks_fetch_failed", "simulated JWKS outage")
            return self.jwks_store.fetch_bytes(url)

        client = CachedJwksClient(
            issuer=ISSUER,
            jwks_uri=JWKS_URI,
            fetch_fn=fetch_fn,
            cache_ttl_seconds=60,
            now_fn=now_fn,
        )
        key = client.get_key(self.kid)
        self.assertEqual(key["kid"], self.kid)
        self.assertEqual(fetch_state["calls"], 1)

        fetch_state["fail"] = True
        clock["t"] = self.now + 30
        self.assertEqual(client.get_key(self.kid)["kid"], self.kid)

        clock["t"] = self.now + 61
        with self.assertRaises(AuthError) as ctx:
            client.get_key(self.kid)
        self.assertEqual(ctx.exception.code, "jwks_unavailable")

    def test_jwks_purge_kid(self) -> None:
        client = CachedJwksClient(
            issuer=ISSUER,
            jwks_uri=JWKS_URI,
            fetch_fn=self.jwks_store.fetch_bytes,
            now_fn=lambda: self.now,
            initial_document=self.jwks_store.document(),
        )
        self.assertEqual(client.get_key(self.kid)["kid"], self.kid)
        client.purge_kid(self.kid)
        self.jwks_store.remove_kid(self.kid)
        with self.assertRaises(AuthError) as ctx:
            client.get_key(self.kid)
        self.assertIn(
            ctx.exception.code,
            {"jwks_unknown_kid", "jwks_invalid", "jwks_unavailable"},
        )

    def test_introspection_cache_purge(self) -> None:
        token = self._mint()
        verified = self.verifier.verify(token)
        self._prime_active(verified)
        self.introspection.require_active(
            token,
            jti=verified.jti,
            expected_iss=ISSUER,
            expected_aud=AUDIENCE,
            expected_sub=verified.sub,
            expected_client_id=CLIENT_ID,
            expected_credential_id="cred-skills-test-1",
            expected_runtime_binding_id="bind-skills-test-1",
            expected_iat=verified.iat,
            expected_exp=verified.exp,
        )
        self.assertEqual(len(self.introspect_backend.calls), 1)
        # Cached hit — no second fetch.
        self.introspection.require_active(
            token,
            jti=verified.jti,
            expected_iss=ISSUER,
            expected_aud=AUDIENCE,
            expected_sub=verified.sub,
            expected_client_id=CLIENT_ID,
            expected_credential_id="cred-skills-test-1",
            expected_runtime_binding_id="bind-skills-test-1",
            expected_iat=verified.iat,
            expected_exp=verified.exp,
        )
        self.assertEqual(len(self.introspect_backend.calls), 1)
        self.introspection.purge_jti(verified.jti)
        self.introspection.require_active(
            token,
            jti=verified.jti,
            expected_iss=ISSUER,
            expected_aud=AUDIENCE,
            expected_sub=verified.sub,
            expected_client_id=CLIENT_ID,
            expected_credential_id="cred-skills-test-1",
            expected_runtime_binding_id="bind-skills-test-1",
            expected_iat=verified.iat,
            expected_exp=verified.exp,
        )
        self.assertEqual(len(self.introspect_backend.calls), 2)

    def test_introspection_inactive_privacy(self) -> None:
        token = self._mint()
        self.introspect_backend.set_inactive()
        with self.assertRaises(AuthError) as ctx:
            self.authenticator.authenticate_for_operation(
                token, operation="skills_run_start"
            )
        self.assertEqual(ctx.exception.code, "auth_revoked")
        # Inactive body must not leak identity fields.
        self.assertEqual(self.introspect_backend.body, {"active": False})

    def test_introspection_missing_binding_field_denied(self) -> None:
        token = self._mint()
        verified = self.verifier.verify(token)
        self.introspect_backend.set_active(
            jti=verified.jti,
            iss=ISSUER,
            sub=verified.sub,
            iat=verified.iat,
            exp=verified.exp,
            omit_fields=["runtime_binding_id"],
        )
        with self.assertRaises(AuthError) as ctx:
            self.authenticator.authenticate_for_operation(
                token, operation="skills_run_start"
            )
        self.assertEqual(ctx.exception.code, "introspection_invalid")

    def test_introspection_wrong_binding_denied(self) -> None:
        token = self._mint()
        verified = self.verifier.verify(token)
        self.introspect_backend.set_active(
            jti=verified.jti,
            iss=ISSUER,
            sub=verified.sub,
            iat=verified.iat,
            exp=verified.exp,
            runtime_binding_id="bind-wrong",
        )
        with self.assertRaises(AuthError) as ctx:
            self.authenticator.authenticate_for_operation(
                token, operation="skills_run_start"
            )
        self.assertEqual(ctx.exception.code, "auth_forbidden")

    def test_introspection_401_fail_closed(self) -> None:
        token = self._mint()
        self.introspect_backend.set_unauthorized()
        with self.assertRaises(AuthError) as ctx:
            self.authenticator.authenticate_for_operation(
                token, operation="skills_tool_invoke"
            )
        self.assertEqual(ctx.exception.code, "introspection_unauthorized")

    def test_introspection_down_fail_closed(self) -> None:
        token = self._mint()
        self.introspect_backend.set_down()
        with self.assertRaises(AuthError) as ctx:
            self.authenticator.authenticate_for_operation(
                token, operation="skills_feedback_submit"
            )
        self.assertEqual(ctx.exception.code, "introspection_unavailable")

    def test_introspection_timeout_fail_closed(self) -> None:
        token = self._mint()
        self.introspect_backend.set_timeout()
        with self.assertRaises(AuthError) as ctx:
            self.authenticator.authenticate_for_operation(
                token, operation="skills_run_complete"
            )
        self.assertEqual(ctx.exception.code, "introspection_unavailable")

    def test_high_risk_operations_match_write_ops(self) -> None:
        expected = {
            "skills_run_start",
            "skills_run_update",
            "skills_run_complete",
            "skills_run_fail",
            "skills_tool_invoke",
            "skills_feedback_submit",
            "skills_trace_candidate_submit",
        }
        self.assertEqual(set(HIGH_RISK_WRITE_OPERATIONS), expected)
        token = self._mint()
        verified = self.verifier.verify(token)
        self._prime_active(verified)
        self.authenticator.authenticate_for_operation(token, operation="skills_list")
        self.assertEqual(len(self.introspect_backend.calls), 0)
        self.authenticator.authenticate_for_operation(
            token, operation="skills_run_start"
        )
        self.assertEqual(len(self.introspect_backend.calls), 1)

    def test_cross_field_aud_mismatch_rejected(self) -> None:
        claims = default_auth_claims(issuer=ISSUER, audience=AUDIENCE, now=self.now)
        claims["audience"] = ["lskills-api", "extra-aud"]
        token = self._mint(claims=claims, payload_overrides={"aud": list(AUDIENCE)})
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(token)
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_signature_tamper_rejected(self) -> None:
        token = self._mint()
        parts = token.split(".")
        claims = default_auth_claims(issuer=ISSUER, audience=AUDIENCE, now=self.now)
        claims["actorId"] = "actor-tampered"
        bad_payload = b64url_encode(
            json.dumps(
                {
                    "iss": ISSUER,
                    "aud": AUDIENCE,
                    "sub": "actor-tampered",
                    "iat": int(self.now),
                    "nbf": int(self.now),
                    "exp": int(self.now) + 900,
                    "jti": str(uuid.uuid4()),
                    PACI_CLAIMS_NAMESPACE: claims,
                },
                separators=(",", ":"),
            ).encode()
        )
        tampered = f"{parts[0]}.{bad_payload}.{parts[2]}"
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(tampered)
        self.assertEqual(ctx.exception.code, "auth_signature_invalid")

    def test_https_required_rejects_http_production(self) -> None:
        with self.assertRaises(AuthError) as ctx:
            assert_https_transport(
                "http://auth.example.com/.well-known/jwks.json",
                label="jwks",
                auth_mode="production",
            )
        self.assertEqual(ctx.exception.code, "auth_https_required")

    def test_https_allows_local_test_loopback_http(self) -> None:
        assert_https_transport(
            "http://127.0.0.1:8080/.well-known/jwks.json",
            label="jwks",
            auth_mode="local-test",
        )

    def test_stub_signer_forbidden_outside_local_test(self) -> None:
        with self.assertRaises(AuthError):
            StubClientAssertionSigner(auth_mode="production")
        with self.assertRaises(AuthError):
            IntrospectionClient(
                introspection_url=INTROSPECT_URL,
                client_id=CLIENT_ID,
                assertion_signer=LocalTestClientAssertionSigner(auth_mode="local-test"),
                auth_mode="production",
            )

    def test_production_factory_requires_secretref_signer(self) -> None:
        env = {
            "LINKSKILLS_AUTH_MODE": "production",
            "LINKSKILLS_PACI_ISSUER": ISSUER,
            "LINKSKILLS_PACI_JWKS_URI": JWKS_URI,
            "LINKSKILLS_PACI_AUDIENCE": "lskills-api",
            "LINKSKILLS_PACI_INTROSPECTION_URL": INTROSPECT_URL,
            "LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID": CLIENT_ID,
        }
        with self.assertRaises(AuthConfigurationError):
            build_paci_authenticator_from_environ(env, jwks=self.jwks)

    def test_secretref_signer_and_assertion_replay(self) -> None:
        key, _jwk = generate_es256_keypair()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "client.pem")
            write_ec_private_key_pem(key, path)
            signer = SecretRefClientAssertionSigner(
                private_key_file=path,
                now_fn=lambda: self.now,
            )
            assertion = signer.mint_assertion(
                audience=INTROSPECT_URL, client_id=CLIENT_ID
            )
            self.assertEqual(assertion.count("."), 2)
            # Simulate replay of a still-valid jti.
            with self.assertRaises(AuthError) as ctx:
                signer.remember_assertion_jti("already-used", until=self.now + 60)
                signer.remember_assertion_jti("already-used", until=self.now + 120)
            self.assertEqual(ctx.exception.code, "auth_assertion_replay")


if __name__ == "__main__":
    unittest.main()
