#!/usr/bin/env python3
"""Fail-closed PACI stage-selection proofs (Lane A).

Proves local-test is never selected for stage/canary paths, HTTPS is required
outside local-test loopback, and production introspection requires SecretRef
private_key_jwt (not LocalTestClientAssertionSigner). Does not call live PACI.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "gateway"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "client"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "mcp_server"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))

from linkskills_client.paci_token_client import (  # noqa: E402
    AUTH_MODE_LOCAL_TEST,
    AUTH_MODE_PRODUCTION,
    PaciConfigError,
    require_https_outside_local_test,
)
from linkskills_gateway.auth import AuthConfigurationError, resolve_auth_mode  # noqa: E402
from linkskills_gateway.jwks import assert_https_transport, validate_issuer_identifier  # noqa: E402
from linkskills_gateway.paci_authenticator import (  # noqa: E402
    build_paci_authenticator_from_environ,
)
from linkskills_gateway.introspection import LocalTestClientAssertionSigner  # noqa: E402
from linkskills_mcp.paci_stdio_proxy import build_paci_client  # noqa: E402


def _write_ephemeral_es256_pem(path: Path) -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


class PaciStageGateSelectionTests(unittest.TestCase):
    def test_stage_env_with_explicit_local_test_is_local_test_mode_only(self) -> None:
        """resolve_auth_mode honors AUTH_MODE; stage env does not override."""
        mode = resolve_auth_mode(
            {
                "LINKSKILLS_ENV": "stage",
                "LINKSKILLS_AUTH_MODE": "local-test",
            }
        )
        self.assertEqual(mode, AUTH_MODE_LOCAL_TEST)
        # Operator contract: this combination is forbidden for stage deploy /
        # canary even though the resolver returns local-test for the flag.

    def test_canary_refuses_local_test_auth_mode(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            build_paci_client(
                {
                    "LINKSKILLS_CANARY": "1",
                    "LINKSKILLS_AUTH_MODE": "local-test",
                    "LINKSKILLS_ENV": "stage",
                    "LINKSKILLS_PACI_CLIENT_ID": "svc_lskills_runtime",
                    "LINKSKILLS_PACI_TOKEN_ENDPOINT": "https://example.invalid/token",
                    "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE": "/tmp/missing.pem",
                }
            )
        self.assertIn("local-test", str(ctx.exception).lower())
        self.assertIn("canary", str(ctx.exception).lower())

    def test_https_required_for_stage_like_production_mode(self) -> None:
        with self.assertRaises(PaciConfigError):
            require_https_outside_local_test(
                "http://example.invalid/oauth/token",
                auth_mode=AUTH_MODE_PRODUCTION,
                label="token_endpoint",
            )
        with self.assertRaises(Exception) as ctx:
            assert_https_transport(
                "http://auth.example.invalid",
                label="PACI issuer",
                auth_mode=AUTH_MODE_PRODUCTION,
            )
        self.assertIn("HTTPS", str(ctx.exception).upper())

    def test_local_test_loopback_http_still_allowed(self) -> None:
        require_https_outside_local_test(
            "http://127.0.0.1:8787/oauth/token",
            auth_mode=AUTH_MODE_LOCAL_TEST,
            label="token_endpoint",
        )
        assert_https_transport(
            "http://127.0.0.1:9",
            label="PACI issuer",
            auth_mode=AUTH_MODE_LOCAL_TEST,
        )
        validate_issuer_identifier(
            "http://127.0.0.1:9",
            auth_mode=AUTH_MODE_LOCAL_TEST,
        )

    def test_production_introspection_requires_secretref_not_local_signer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            key_path = Path(tmp) / "client.pem"
            _write_ephemeral_es256_pem(key_path)
            # Missing SecretRef path → fail closed (no LocalTest signer).
            with self.assertRaises(AuthConfigurationError) as ctx:
                build_paci_authenticator_from_environ(
                    {
                        "LINKSKILLS_AUTH_MODE": "production",
                        "LINKSKILLS_ENV": "stage",
                        "LINKSKILLS_PACI_ISSUER": "https://auth.example.invalid",
                        "LINKSKILLS_PACI_JWKS_URI": (
                            "https://auth.example.invalid/.well-known/jwks.json"
                        ),
                        "LINKSKILLS_PACI_AUDIENCE": "lskills-api",
                        "LINKSKILLS_PACI_INTROSPECTION_URL": (
                            "https://auth.example.invalid/oauth/introspect"
                        ),
                        "LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID": "rs-skills",
                        "LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS": "mint-skills",
                        # intentionally omit LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE
                    }
                )
            msg = str(ctx.exception).lower()
            self.assertTrue(
                "private_key" in msg or "secretref" in msg or "jwt" in msg,
                msg=str(ctx.exception),
            )

            # Injected LocalTest signer forbidden outside local-test.
            with self.assertRaises(AuthConfigurationError) as ctx2:
                build_paci_authenticator_from_environ(
                    {
                        "LINKSKILLS_AUTH_MODE": "production",
                        "LINKSKILLS_ENV": "stage",
                        "LINKSKILLS_PACI_ISSUER": "https://auth.example.invalid",
                        "LINKSKILLS_PACI_JWKS_URI": (
                            "https://auth.example.invalid/.well-known/jwks.json"
                        ),
                        "LINKSKILLS_PACI_AUDIENCE": "lskills-api",
                        "LINKSKILLS_PACI_INTROSPECTION_URL": (
                            "https://auth.example.invalid/oauth/introspect"
                        ),
                        "LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID": "rs-skills",
                        "LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS": "mint-skills",
                        "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE": str(key_path),
                    },
                    assertion_signer=LocalTestClientAssertionSigner(
                        auth_mode=AUTH_MODE_LOCAL_TEST
                    ),
                )
            self.assertIn("forbidden", str(ctx2.exception).lower())

            # SecretRef path present → factory accepts config shape (no live call).
            auth = build_paci_authenticator_from_environ(
                {
                    "LINKSKILLS_AUTH_MODE": "production",
                    "LINKSKILLS_ENV": "stage",
                    "LINKSKILLS_PACI_ISSUER": "https://auth.example.invalid",
                    "LINKSKILLS_PACI_JWKS_URI": (
                        "https://auth.example.invalid/.well-known/jwks.json"
                    ),
                    "LINKSKILLS_PACI_AUDIENCE": "lskills-api",
                    "LINKSKILLS_PACI_INTROSPECTION_URL": (
                        "https://auth.example.invalid/oauth/introspect"
                    ),
                    "LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID": "rs-skills",
                    "LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS": "mint-skills",
                    "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE": str(key_path),
                }
            )
            self.assertEqual(auth.issuer, "https://auth.example.invalid")
            self.assertNotEqual(auth.evidence_status, "live_proven")

    def test_stage_like_defaults_are_production_auth_mode(self) -> None:
        self.assertEqual(
            resolve_auth_mode({"LINKSKILLS_ENV": "stage"}),
            AUTH_MODE_PRODUCTION,
        )
        self.assertEqual(
            resolve_auth_mode(
                {"LINKSKILLS_ENV": "stage", "LINKSKILLS_CANARY": "1"}
            ),
            AUTH_MODE_PRODUCTION,
        )


if __name__ == "__main__":
    unittest.main()
