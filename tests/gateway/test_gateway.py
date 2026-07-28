#!/usr/bin/env python3
"""Gateway unit tests: frozen claims, crypto authenticity, unsigned isolation."""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path

os.environ.setdefault(
    "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
    "linkskills-local-eval-runner-issuer-key-not-for-production",
)
os.environ.setdefault("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "allow_unproven")

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATHS = [
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "mcp_server",
    REPO_ROOT / "packages" / "client",
    REPO_ROOT / "packages" / "librarian_domain",
    REPO_ROOT / "packages" / "eval_runner",
    REPO_ROOT / "packages" / "tool_runtime",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
]
for path in PACKAGE_PATHS:
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import (  # noqa: E402
    CLAIM_CONTRACT_VERSION,
    AuthConfigurationError,
    AuthError,
    LocalUnsignedClaimsVerifier,
    PlatformClaimsVerifier,
    load_platform_claim_fixture,
    resolve_claims_verifier,
    verify_frozen_auth_claims_schema,
)
from linkskills_gateway.auth_testing import (  # noqa: E402
    LocalTestHmacAuthenticator,
    mint_fake_token,
    mint_platform_token,
    mint_test_bearer,
    production_test_verifier,
)
from linkskills_gateway.server import create_server  # noqa: E402
from linkskills_gateway.service import ServiceError, SkillsGatewayService  # noqa: E402
from linkskills_tool_runtime.descriptor import load_tool_descriptor  # noqa: E402


def _platform_claims(**overrides):
    now = int(time.time())
    base = {
        "claimContractVersion": CLAIM_CONTRACT_VERSION,
        "actorId": "actor-1",
        "actorKind": "service",
        "runtimeBindingId": "bind-1",
        "credentialId": "cred-1",
        "orgId": "org-1",
        "internal": True,
        "serviceScopes": ["lskills", "linkplatform"],
        "permittedOperations": ["read", "execute", "skills:read", "skills:write"],
        "issuedAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(now - 60)),
        "expiresAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(now + 3600)),
        "issuer": "linkplatform-issuer",
        "audience": ["lskills-api"],
        "correlationId": "corr-1",
    }
    base.update(overrides)
    return base


class LocalUnsignedAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verifier = LocalUnsignedClaimsVerifier()

    def test_frozen_schema_hashes(self) -> None:
        meta = verify_frozen_auth_claims_schema()
        self.assertEqual(meta["contract"], CLAIM_CONTRACT_VERSION)
        self.assertEqual(meta["package"], "0.2.1")

    def test_valid_unsigned_token_accepted_in_local_test(self) -> None:
        token = mint_platform_token(_platform_claims())
        claims = self.verifier.verify(f"Bearer {token}")
        self.assertEqual(claims.actor_id, "actor-1")
        self.assertEqual(claims.actor_kind, "service")
        self.assertTrue(claims.may_write())

    def test_actor_kind_agent_rejected(self) -> None:
        token = mint_platform_token(_platform_claims(actorKind="agent"))
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {token}")
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_snake_case_fields_rejected(self) -> None:
        claims = _platform_claims()
        claims["actor_id"] = claims.pop("actorId")
        token = mint_platform_token(claims)
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {token}")
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_unknown_fields_rejected(self) -> None:
        token = mint_platform_token(_platform_claims(extraField="nope"))
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {token}")
        self.assertEqual(ctx.exception.code, "auth_invalid")

    def test_wrong_contract_version_rejected(self) -> None:
        token = mint_platform_token(_platform_claims(claimContractVersion="1.0.0"))
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {token}")
        self.assertEqual(ctx.exception.code, "auth_contract_mismatch")

    def test_fake_token_rejected(self) -> None:
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify("Bearer fake.abc")
        self.assertEqual(ctx.exception.code, "auth_unsupported")

    def test_missing_auth_rejected(self) -> None:
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(None)
        self.assertEqual(ctx.exception.code, "auth_missing")

    def test_body_actor_spoof_rejected(self) -> None:
        token = mint_platform_token(_platform_claims())
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(
                f"Bearer {token}",
                request_payload={"actorId": "attacker", "skill_id": "x"},
            )
        self.assertEqual(ctx.exception.code, "auth_spoof_rejected")

    def test_override_headers_rejected(self) -> None:
        token = mint_platform_token(_platform_claims())
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(
                f"Bearer {token}",
                request_headers={"X-Actor-Id": "attacker"},
            )
        self.assertEqual(ctx.exception.code, "auth_spoof_rejected")

    def test_expired_fixture_with_injected_clock(self) -> None:
        fixture = load_platform_claim_fixture("reject-expired")
        token = mint_platform_token(fixture["claims"])
        verifier = LocalUnsignedClaimsVerifier(
            expected_audience=fixture["context"]["expectedAudience"],
            required_service=fixture["context"]["requiredService"],
        )
        with self.assertRaises(AuthError) as ctx:
            verifier.verify(
                f"Bearer {token}",
                now=fixture["context"]["now"],
                credential_status=fixture["context"]["credentialStatus"],
            )
        self.assertEqual(ctx.exception.code, "auth_expired")

    def test_vendored_lskills_fixture_accepted_with_fixture_now(self) -> None:
        fixture = load_platform_claim_fixture("accept-valid-lskills")
        token = mint_platform_token(fixture["claims"])
        claims = self.verifier.verify(
            f"Bearer {token}",
            now=fixture["context"]["now"],
        )
        self.assertEqual(claims.actor_id, fixture["claims"]["actorId"])
        self.assertEqual(claims.claim_contract_version, CLAIM_CONTRACT_VERSION)


class ProductionCryptoAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hmac = LocalTestHmacAuthenticator()
        self.verifier = production_test_verifier(authenticator=self.hmac)

    def test_construction_without_authenticator_fails_closed(self) -> None:
        with self.assertRaises(AuthConfigurationError):
            PlatformClaimsVerifier()

    def test_resolve_production_without_env_fails_closed(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "LINKSKILLS_PLATFORM_AUTHENTICATOR"}
        env["LINKSKILLS_AUTH_MODE"] = "production"
        env.pop("LINKSKILLS_PLATFORM_AUTHENTICATOR", None)
        with self.assertRaises(AuthConfigurationError):
            resolve_claims_verifier(environ=env)

    def test_signed_token_accepted(self) -> None:
        token = self.hmac.mint(_platform_claims())
        claims = self.verifier.verify(f"Bearer {token}")
        self.assertEqual(claims.actor_id, "actor-1")

    def test_self_minted_unsigned_canonical_bearer_rejected(self) -> None:
        unsigned = mint_platform_token(_platform_claims())
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {unsigned}")
        self.assertEqual(ctx.exception.code, "auth_unsigned_rejected")

    def test_raw_json_bearer_rejected(self) -> None:
        raw = json.dumps(_platform_claims(), separators=(",", ":"), sort_keys=True)
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {raw}")
        self.assertEqual(ctx.exception.code, "auth_unsigned_rejected")

    def test_fake_token_rejected(self) -> None:
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {mint_fake_token({'actorId': 'x'})}")
        self.assertEqual(ctx.exception.code, "auth_unsupported")

    def test_wrong_issuer_rejected(self) -> None:
        token = self.hmac.mint(_platform_claims(issuer="evil-issuer"))
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {token}")
        self.assertEqual(ctx.exception.code, "auth_forbidden")
        self.assertIn("issuer", ctx.exception.message.lower())

    def test_wrong_audience_rejected(self) -> None:
        token = self.hmac.mint(_platform_claims(audience=["other-api"]))
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {token}")
        self.assertEqual(ctx.exception.code, "auth_forbidden")
        self.assertIn("audience", ctx.exception.message.lower())

    def test_expired_token_rejected(self) -> None:
        now = int(time.time())
        token = self.hmac.mint(
            _platform_claims(
                issuedAt=time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(now - 7200)),
                expiresAt=time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(now - 3600)),
            )
        )
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {token}")
        self.assertEqual(ctx.exception.code, "auth_expired")

    def test_revoked_token_rejected(self) -> None:
        hmac_auth = LocalTestHmacAuthenticator(
            credential_status_by_id={"cred-revoked": "revoked"}
        )
        verifier = production_test_verifier(authenticator=hmac_auth)
        token = hmac_auth.mint(_platform_claims(credentialId="cred-revoked"))
        with self.assertRaises(AuthError) as ctx:
            verifier.verify(f"Bearer {token}")
        self.assertEqual(ctx.exception.code, "auth_revoked")

    def test_wrong_operation_rejected(self) -> None:
        token = self.hmac.mint(
            _platform_claims(permittedOperations=["read", "skills:read"])
        )
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(
                f"Bearer {token}",
                required_operation="skills:write",
            )
        self.assertEqual(ctx.exception.code, "auth_forbidden")
        self.assertIn("not permitted", ctx.exception.message.lower())

    def test_tampered_signature_rejected(self) -> None:
        token = self.hmac.mint(_platform_claims())
        parts = token.rsplit(".", 1)
        self.assertEqual(len(parts), 2)
        # Replace MAC with a same-length invalid digest (base64url of zeros).
        bad_mac = "A" * len(parts[1])
        if bad_mac == parts[1]:
            bad_mac = "B" * len(parts[1])
        bad = f"{parts[0]}.{bad_mac}"
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {bad}")
        self.assertIn(ctx.exception.code, {"auth_signature_invalid", "auth_malformed"})

    def test_mint_platform_token_not_exported_from_package_root(self) -> None:
        import linkskills_gateway as gw

        self.assertFalse(hasattr(gw, "mint_platform_token"))


class ServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SkillsGatewayService(repo_root=REPO_ROOT)
        self.actor = LocalUnsignedClaimsVerifier().verify(f"Bearer {mint_test_bearer()}")

    def test_skills_list(self) -> None:
        env = self.service.dispatch("skills_list", {}, actor=self.actor)
        self.assertIsNone(env["error"])
        self.assertGreater(env["data"]["count"], 0)
        ids = {s["skill_id"] for s in env["data"]["skills"]}
        self.assertIn("git-safeguard", ids)

    def test_tool_invoke_dry_run_resolves(self) -> None:
        env = self.service.dispatch(
            "skills_tool_invoke",
            {"tool_id": "text-echo", "dry_run": True, "argv": ["hi"]},
            actor=self.actor,
        )
        self.assertIsNone(env["error"])
        self.assertTrue(env["data"]["dry_run"])
        self.assertEqual(env["data"]["output"]["mode"], "dry_run")
        self.assertNotEqual(env["data"]["output"].get("mode"), "live_echo")

    def test_tool_invoke_live_without_hash_fails_closed(self) -> None:
        with self.assertRaises(ServiceError) as ctx:
            self.service.dispatch(
                "skills_tool_invoke",
                {"tool_id": "text-echo", "dry_run": False, "version": "1.0.0", "argv": ["hi"]},
                actor=self.actor,
            )
        self.assertEqual(ctx.exception.code, "tool_hash_required")
        self.assertNotIn("live_echo", ctx.exception.message)

    def test_tool_invoke_live_adapter_not_live_echo(self) -> None:
        descriptor = load_tool_descriptor(REPO_ROOT / "tools" / "text-echo")
        env = self.service.dispatch(
            "skills_tool_invoke",
            {
                "tool_id": "text-echo",
                "dry_run": False,
                "version": descriptor.version,
                "source_hash": descriptor.source_hash,
                "argv": ["HELLO_LIVE"],
            },
            actor=self.actor,
        )
        self.assertIsNone(env["error"], env)
        self.assertFalse(env["data"]["dry_run"])
        self.assertEqual(env["data"]["output"]["mode"], "live_adapter")
        self.assertIn("HELLO_LIVE", env["data"]["output"]["stdout"])
        self.assertNotIn("live_echo", json.dumps(env["data"]))


class HttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=SkillsGatewayService(repo_root=REPO_ROOT),
            verifier=LocalUnsignedClaimsVerifier(),
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.token = mint_test_bearer()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def test_health(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", "/health")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        conn.close()

    def test_skills_list_http(self) -> None:
        body = json.dumps({})
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            "/v1/skills_list",
            body=body,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
            },
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(resp.status, 200, payload)
        self.assertIsNone(payload.get("error"))
        conn.close()


class RunLifecycleGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = {
            "skills": [
                {
                    "skill_id": "usable-demo",
                    "version": "1.0.0",
                    "description": "usable demo",
                    "format_profile": "heavy",
                    "eval_suite_ref": "",
                    "certification_state": "usable",
                    "release_hash": "release-usable-1",
                    "profile_hash": "profile-usable-1",
                    "compatible_runtime_profiles": ["cursor-macos"],
                },
                {
                    "skill_id": "draft-demo",
                    "version": "0.0.1",
                    "description": "draft demo",
                    "format_profile": "heavy",
                    "eval_suite_ref": "",
                    "certification_state": "draft",
                    "compatible_runtime_profiles": ["cursor-macos"],
                },
            ]
        }
        self.service = SkillsGatewayService(
            repo_root=REPO_ROOT,
            catalog_index=self.catalog,
        )
        self.owner = LocalUnsignedClaimsVerifier().verify(
            f"Bearer {mint_test_bearer({'actor_id': 'owner', 'org_id': 'org-a'})}"
        )
        self.intruder = LocalUnsignedClaimsVerifier().verify(
            f"Bearer {mint_test_bearer({'actor_id': 'intruder', 'org_id': 'org-b'})}"
        )

    def test_rejects_draft_run_start(self) -> None:
        with self.assertRaises(ServiceError) as ctx:
            self.service.dispatch(
                "skills_run_start",
                {"skill_id": "draft-demo"},
                actor=self.owner,
            )
        self.assertEqual(ctx.exception.code, "skill_not_runnable")

    def test_rejects_release_hash_mismatch(self) -> None:
        with self.assertRaises(ServiceError) as ctx:
            self.service.dispatch(
                "skills_run_start",
                {
                    "skill_id": "usable-demo",
                    "release_hash": "wrong-release",
                    "runtime_profile_tags": ["cursor-macos"],
                },
                actor=self.owner,
            )
        self.assertEqual(ctx.exception.code, "release_hash_mismatch")

    def test_rejects_incompatible_profile(self) -> None:
        with self.assertRaises(ServiceError) as ctx:
            self.service.dispatch(
                "skills_run_start",
                {
                    "skill_id": "usable-demo",
                    "runtime_profile_tags": ["codex-linux"],
                },
                actor=self.owner,
            )
        self.assertEqual(ctx.exception.code, "profile_incompatible")

    def test_usable_run_start_ok(self) -> None:
        env = self.service.dispatch(
            "skills_run_start",
            {
                "skill_id": "usable-demo",
                "release_hash": "release-usable-1",
                "profile_hash": "profile-usable-1",
                "runtime_profile_tags": ["cursor-macos"],
            },
            actor=self.owner,
        )
        self.assertIsNone(env["error"])
        self.assertEqual(env["data"]["skill_id"], "usable-demo")

    def test_feedback_rejects_wrong_owner(self) -> None:
        started = self.service.dispatch(
            "skills_run_start",
            {
                "skill_id": "usable-demo",
                "runtime_profile_tags": ["cursor-macos"],
            },
            actor=self.owner,
        )
        run_id = started["run_id"]
        with self.assertRaises(ServiceError) as ctx:
            self.service.dispatch(
                "skills_feedback_submit",
                {
                    "skill_id": "usable-demo",
                    "run_id": run_id,
                    "kind": "correction",
                    "notes": "stolen",
                },
                actor=self.intruder,
            )
        self.assertEqual(ctx.exception.code, "auth_forbidden")


if __name__ == "__main__":
    unittest.main()
