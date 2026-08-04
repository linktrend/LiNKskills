"""Introspection mint-client vs RS assertion-client separation (Lane C).

Deliberately uses distinct Cursor mint-client and Skills resource-server
assertion-client IDs so the old conflation (validate response client_id
against LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID) cannot pass.
"""

from __future__ import annotations

import tempfile
import unittest
from typing import Any
from urllib.parse import parse_qs

from linkskills_gateway.auth import AuthConfigurationError, AuthError
from linkskills_gateway.introspection import (
    IntrospectionClient,
    LocalTestClientAssertionSigner,
    SecretRefClientAssertionSigner,
)
from linkskills_gateway.jwks import StaticJwksProvider
from linkskills_gateway.paci_authenticator import (
    ENV_PACI_TRUSTED_MINT_CLIENT_IDS,
    PaciJwtAuthenticator,
    build_paci_authenticator_from_environ,
)
from linkskills_gateway.paci_jwt import PaciJwtVerifier

from tests.gateway.paci_fakes import (
    FakeIntrospectionBackend,
    InMemoryJwksStore,
    generate_es256_keypair,
    mint_paci_token,
    write_ec_private_key_pem,
)


ISSUER = "https://auth.stage.linkplatform.linktrend.dev"
JWKS_URI = f"{ISSUER}/.well-known/jwks.json"
AUDIENCE = ["lskills-api"]
INTROSPECT_URL = f"{ISSUER}/oauth/introspect"

# Distinct principals — must never be treated as interchangeable.
RS_ASSERTION_CLIENT_ID = "skills-rs-assertion-client"
CURSOR_MINT_CLIENT_ID = "cursor-mint-client"


class IntrospectionClientBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 1_800_000_000.0
        self.private_key, self.jwk = generate_es256_keypair()
        self.kid = str(self.jwk["kid"])
        self.jwks = StaticJwksProvider(InMemoryJwksStore([self.jwk]).document())
        self.verifier = PaciJwtVerifier(
            issuer=ISSUER,
            audiences=AUDIENCE,
            jwks=self.jwks,
            now_fn=lambda: self.now,
        )
        self.backend = FakeIntrospectionBackend()
        self.introspection = IntrospectionClient(
            introspection_url=INTROSPECT_URL,
            client_id=RS_ASSERTION_CLIENT_ID,
            assertion_signer=LocalTestClientAssertionSigner(auth_mode="local-test"),
            fetch_fn=self.backend.fetch,
            now_fn=lambda: self.now,
            auth_mode="local-test",
            required_scopes=["lskills"],
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

    def _prime(self, verified: Any, *, client_id: str) -> None:
        self.backend.set_active(
            jti=verified.jti,
            iss=ISSUER,
            sub=verified.sub,
            aud=sorted(verified.aud),
            client_id=client_id,
            credential_id=str(verified.claims.get("credentialId")),
            runtime_binding_id=str(verified.claims.get("runtimeBindingId")),
            iat=verified.iat,
            exp=verified.exp,
            scope="lskills",
        )

    def test_ids_are_deliberately_distinct(self) -> None:
        self.assertNotEqual(RS_ASSERTION_CLIENT_ID, CURSOR_MINT_CLIENT_ID)

    def test_assertion_request_uses_rs_client_id_not_mint(self) -> None:
        token = self._mint()
        verified = self.verifier.verify(token)
        self._prime(verified, client_id=CURSOR_MINT_CLIENT_ID)
        self.introspection.require_active(
            token,
            jti=verified.jti,
            expected_iss=ISSUER,
            expected_aud=AUDIENCE,
            expected_sub=verified.sub,
            trusted_mint_client_ids=[CURSOR_MINT_CLIENT_ID],
            expected_credential_id="cred-skills-test-1",
            expected_runtime_binding_id="bind-skills-test-1",
            expected_iat=verified.iat,
            expected_exp=verified.exp,
        )
        self.assertEqual(len(self.backend.calls), 1)
        form = parse_qs(self.backend.calls[0]["body"].decode("utf-8"))
        self.assertEqual(form["client_id"], [RS_ASSERTION_CLIENT_ID])
        self.assertNotEqual(form["client_id"], [CURSOR_MINT_CLIENT_ID])

    def test_old_conflation_fails_when_mint_differs_from_assertion(self) -> None:
        """Simulate pre-Lane-C binding: expect response client_id == RS assertion id.

        Active response carries Cursor mint id; that exact-match against the RS
        assertion id must deny.
        """
        token = self._mint()
        verified = self.verifier.verify(token)
        self._prime(verified, client_id=CURSOR_MINT_CLIENT_ID)
        with self.assertRaises(AuthError) as ctx:
            # Old API shape: single expected_client_id == assertion identity.
            # Emulate via allow-list that only contains the RS assertion id.
            self.introspection.require_active(
                token,
                jti=verified.jti,
                expected_iss=ISSUER,
                expected_aud=AUDIENCE,
                expected_sub=verified.sub,
                trusted_mint_client_ids=[RS_ASSERTION_CLIENT_ID],
                expected_credential_id="cred-skills-test-1",
                expected_runtime_binding_id="bind-skills-test-1",
                expected_iat=verified.iat,
                expected_exp=verified.exp,
            )
        self.assertEqual(ctx.exception.code, "auth_forbidden")
        self.assertIn("trusted mint", ctx.exception.message)

    def test_correct_separation_passes_with_mint_allow_list(self) -> None:
        token = self._mint()
        verified = self.verifier.verify(token)
        self._prime(verified, client_id=CURSOR_MINT_CLIENT_ID)
        result = self.introspection.require_active(
            token,
            jti=verified.jti,
            expected_iss=ISSUER,
            expected_aud=AUDIENCE,
            expected_sub=verified.sub,
            trusted_mint_client_ids=[CURSOR_MINT_CLIENT_ID],
            expected_credential_id="cred-skills-test-1",
            expected_runtime_binding_id="bind-skills-test-1",
            expected_iat=verified.iat,
            expected_exp=verified.exp,
        )
        self.assertTrue(result.active)
        self.assertEqual(result.client_id, CURSOR_MINT_CLIENT_ID)

    def test_authenticator_old_conflation_denies_high_risk(self) -> None:
        """Authenticator wired like old code (mint list = assertion id) denies."""
        token = self._mint()
        verified = self.verifier.verify(token)
        self._prime(verified, client_id=CURSOR_MINT_CLIENT_ID)
        conflated = PaciJwtAuthenticator(
            issuer=ISSUER,
            audiences=AUDIENCE,
            jwks=self.jwks,
            introspection=self.introspection,
            now_fn=lambda: self.now,
            introspection_client_id=RS_ASSERTION_CLIENT_ID,
            trusted_mint_client_ids=[RS_ASSERTION_CLIENT_ID],  # old conflation
            auth_mode="local-test",
        )
        with self.assertRaises(AuthError) as ctx:
            conflated.authenticate_for_operation(
                token, operation="skills_run_start"
            )
        self.assertEqual(ctx.exception.code, "auth_forbidden")

    def test_authenticator_separated_principals_accept_high_risk(self) -> None:
        token = self._mint()
        verified = self.verifier.verify(token)
        self._prime(verified, client_id=CURSOR_MINT_CLIENT_ID)
        auth = PaciJwtAuthenticator(
            issuer=ISSUER,
            audiences=AUDIENCE,
            jwks=self.jwks,
            introspection=self.introspection,
            now_fn=lambda: self.now,
            introspection_client_id=RS_ASSERTION_CLIENT_ID,
            trusted_mint_client_ids=[CURSOR_MINT_CLIENT_ID],
            auth_mode="local-test",
        )
        result = auth.authenticate_for_operation(
            token, operation="skills_run_start"
        )
        self.assertEqual(result.credential_status, "active")

    def test_empty_mint_allow_list_fail_closed(self) -> None:
        token = self._mint()
        verified = self.verifier.verify(token)
        self._prime(verified, client_id=CURSOR_MINT_CLIENT_ID)
        with self.assertRaises(AuthError) as ctx:
            self.introspection.require_active(
                token,
                jti=verified.jti,
                expected_iss=ISSUER,
                expected_aud=AUDIENCE,
                expected_sub=verified.sub,
                trusted_mint_client_ids=[],
                expected_credential_id="cred-skills-test-1",
                expected_runtime_binding_id="bind-skills-test-1",
                expected_iat=verified.iat,
                expected_exp=verified.exp,
            )
        self.assertEqual(ctx.exception.code, "auth_config")

    def test_authenticator_missing_mint_allow_list_fail_closed(self) -> None:
        token = self._mint()
        auth = PaciJwtAuthenticator(
            issuer=ISSUER,
            audiences=AUDIENCE,
            jwks=self.jwks,
            introspection=self.introspection,
            now_fn=lambda: self.now,
            introspection_client_id=RS_ASSERTION_CLIENT_ID,
            trusted_mint_client_ids=None,
            auth_mode="local-test",
        )
        with self.assertRaises(AuthError) as ctx:
            auth.authenticate_for_operation(token, operation="skills_run_start")
        self.assertEqual(ctx.exception.code, "auth_config")
        self.assertIn(ENV_PACI_TRUSTED_MINT_CLIENT_IDS, ctx.exception.message)

    def test_production_factory_missing_trusted_mint_fail_closed(self) -> None:
        env = {
            "LINKSKILLS_AUTH_MODE": "production",
            "LINKSKILLS_PACI_ISSUER": ISSUER,
            "LINKSKILLS_PACI_JWKS_URI": JWKS_URI,
            "LINKSKILLS_PACI_AUDIENCE": "lskills-api",
            "LINKSKILLS_PACI_INTROSPECTION_URL": INTROSPECT_URL,
            "LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID": RS_ASSERTION_CLIENT_ID,
        }
        with self.assertRaises(AuthConfigurationError) as ctx:
            build_paci_authenticator_from_environ(env, jwks=self.jwks)
        self.assertIn(ENV_PACI_TRUSTED_MINT_CLIENT_IDS, str(ctx.exception))

    def test_production_factory_accepts_separated_ids_with_secretref(self) -> None:
        key, _jwk = generate_es256_keypair()
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/rs-assertion.pem"
            write_ec_private_key_pem(key, path)
            env = {
                "LINKSKILLS_AUTH_MODE": "production",
                "LINKSKILLS_PACI_ISSUER": ISSUER,
                "LINKSKILLS_PACI_JWKS_URI": JWKS_URI,
                "LINKSKILLS_PACI_AUDIENCE": "lskills-api",
                "LINKSKILLS_PACI_INTROSPECTION_URL": INTROSPECT_URL,
                "LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID": RS_ASSERTION_CLIENT_ID,
                "LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS": CURSOR_MINT_CLIENT_ID,
                "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE": path,
            }
            auth = build_paci_authenticator_from_environ(env, jwks=self.jwks)
            self.assertEqual(auth._introspection_client_id, RS_ASSERTION_CLIENT_ID)
            self.assertEqual(
                auth._trusted_mint_client_ids, frozenset({CURSOR_MINT_CLIENT_ID})
            )
            self.assertIsNotNone(auth._introspection)
            self.assertEqual(auth._introspection.client_id, RS_ASSERTION_CLIENT_ID)
            self.assertIsInstance(
                auth._introspection.assertion_signer, SecretRefClientAssertionSigner
            )

    def test_untrusted_mint_client_denied(self) -> None:
        token = self._mint()
        verified = self.verifier.verify(token)
        self._prime(verified, client_id="hostile-mint-client")
        with self.assertRaises(AuthError) as ctx:
            self.introspection.require_active(
                token,
                jti=verified.jti,
                expected_iss=ISSUER,
                expected_aud=AUDIENCE,
                expected_sub=verified.sub,
                trusted_mint_client_ids=[CURSOR_MINT_CLIENT_ID],
                expected_credential_id="cred-skills-test-1",
                expected_runtime_binding_id="bind-skills-test-1",
                expected_iat=verified.iat,
                expected_exp=verified.exp,
            )
        self.assertEqual(ctx.exception.code, "auth_forbidden")


if __name__ == "__main__":
    unittest.main()
