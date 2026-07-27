#!/usr/bin/env python3
"""Gateway unit tests: auth spoof rejection, operations, HTTP surface."""

from __future__ import annotations

import json
import sys
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATHS = [
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "mcp_server",
    REPO_ROOT / "packages" / "client",
    REPO_ROOT / "packages" / "librarian_domain",
    REPO_ROOT / "packages" / "eval_runner",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
]
for path in PACKAGE_PATHS:
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import (  # noqa: E402
    AuthError,
    FakePlatformClaimsVerifier,
    mint_fake_token,
)
from linkskills_gateway.server import create_server  # noqa: E402
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402


def _claims(**overrides):
    base = {
        "actor_id": "actor-1",
        "actor_kind": "human",
        "org_id": "org-1",
        "scopes": ["skills:read", "skills:write"],
        "exp": int(time.time()) + 3600,
        "credential_id": "cred-1",
    }
    base.update(overrides)
    return base


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verifier = FakePlatformClaimsVerifier()

    def test_valid_fake_token_accepted(self) -> None:
        token = mint_fake_token(_claims())
        claims = self.verifier.verify(f"Bearer {token}")
        self.assertEqual(claims.actor_id, "actor-1")

    def test_missing_auth_rejected(self) -> None:
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(None)
        self.assertEqual(ctx.exception.code, "auth_missing")

    def test_body_actor_spoof_rejected(self) -> None:
        token = mint_fake_token(_claims())
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(
                f"Bearer {token}",
                request_payload={"actor_id": "attacker", "skill_id": "x"},
            )
        self.assertEqual(ctx.exception.code, "auth_spoof_rejected")

    def test_override_headers_rejected(self) -> None:
        token = mint_fake_token(_claims())
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(
                f"Bearer {token}",
                request_headers={"X-Actor-Id": "attacker"},
            )
        self.assertEqual(ctx.exception.code, "auth_spoof_rejected")

    def test_expired_rejected(self) -> None:
        token = mint_fake_token(_claims(exp=int(time.time()) - 10))
        with self.assertRaises(AuthError) as ctx:
            self.verifier.verify(f"Bearer {token}")
        self.assertEqual(ctx.exception.code, "auth_expired")


class ServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SkillsGatewayService(repo_root=REPO_ROOT)
        self.actor = FakePlatformClaimsVerifier().verify(
            f"Bearer {mint_fake_token(_claims())}"
        )

    def test_skills_list(self) -> None:
        env = self.service.dispatch("skills_list", {}, actor=self.actor)
        self.assertIsNone(env["error"])
        self.assertGreater(env["data"]["count"], 0)
        ids = {s["skill_id"] for s in env["data"]["skills"]}
        self.assertIn("git-safeguard", ids)

    def test_fragment_levels_0_to_5(self) -> None:
        for level in range(0, 6):
            env = self.service.dispatch(
                "skills_fragment_get",
                {"skill_id": "git-safeguard", "disclosure_level": level},
                actor=self.actor,
            )
            self.assertEqual(env["data"]["disclosure_level"], level)
            self.assertTrue(env["data"]["content"])

    def test_level_6_requires_explicit(self) -> None:
        with self.assertRaises(Exception) as ctx:
            self.service.dispatch(
                "skills_fragment_get",
                {"skill_id": "git-safeguard", "disclosure_level": 6},
                actor=self.actor,
            )
        self.assertEqual(ctx.exception.code, "full_pack_requires_explicit")

    def test_tool_invoke_dry_run_default(self) -> None:
        env = self.service.dispatch(
            "skills_tool_invoke",
            {
                "skill_id": "git-safeguard",
                "tool_id": "git-safeguard.echo",
                "input": {"x": 1},
            },
            actor=self.actor,
        )
        self.assertTrue(env["data"]["dry_run"])
        self.assertIn("tool_invoke_dry_run", env["warnings"])

    def test_run_start_idempotency(self) -> None:
        first = self.service.dispatch(
            "skills_run_start",
            {"skill_id": "git-safeguard"},
            actor=self.actor,
            idempotency_key="idem-1",
        )
        second = self.service.dispatch(
            "skills_run_start",
            {"skill_id": "git-safeguard"},
            actor=self.actor,
            idempotency_key="idem-1",
        )
        self.assertEqual(first["data"]["run_id"], second["data"]["run_id"])
        self.assertIn("idempotent_replay", second["warnings"])


class HttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SkillsGatewayService(repo_root=REPO_ROOT)
        self.httpd = create_server("127.0.0.1", 0, service=self.service)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.token = mint_fake_token(_claims())

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def _post(self, operation: str, body: dict, headers: dict | None = None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        if headers:
            hdrs.update(headers)
        conn.request("POST", f"/v1/{operation}", body=json.dumps(body), headers=hdrs)
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        conn.close()
        return resp.status, json.loads(raw)

    def test_health(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", "/health")
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        conn.close()
        self.assertEqual(resp.status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_http_skills_list(self) -> None:
        status, payload = self._post("skills_list", {"params": {}})
        self.assertEqual(status, 200)
        self.assertGreater(payload["data"]["count"], 0)

    def test_http_rejects_actor_override_header(self) -> None:
        status, payload = self._post(
            "skills_list",
            {"params": {}},
            headers={"X-Actor-Id": "attacker"},
        )
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"]["code"], "auth_spoof_rejected")


if __name__ == "__main__":
    unittest.main()
