#!/usr/bin/env python3
"""MCP server tests — parity, auth fail-closed, canary crypto identity."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "mcp_server",
    REPO_ROOT / "packages" / "client",
    REPO_ROOT / "packages" / "librarian_domain",
    REPO_ROOT / "packages" / "eval_runner",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import (  # noqa: E402
    AuthConfigurationError,
    AuthError,
    LocalUnsignedClaimsVerifier,
)
from linkskills_gateway.auth_testing import (  # noqa: E402
    mint_signed_test_bearer,
    mint_test_bearer,
    production_test_verifier,
)
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402
from linkskills_mcp.server import SkillsMcpServer, resolve_canary_default_actor  # noqa: E402


def _claims():
    return {
        "actor_id": "actor-mcp",
        "actor_kind": "service",
        "org_id": "org-1",
        "scopes": ["skills:read", "skills:write"],
        "exp": int(time.time()) + 3600,
    }


class McpParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SkillsGatewayService(repo_root=REPO_ROOT)
        self.local = LocalUnsignedClaimsVerifier()
        self.mcp = SkillsMcpServer(service=self.service, verifier=self.local)
        self.token = mint_test_bearer(_claims())

    def test_tools_list_includes_skills_operations(self) -> None:
        tools = {t["name"] for t in self.mcp.list_tools()}
        self.assertIn("skills_list", tools)
        self.assertIn("skills_run_start", tools)
        self.assertIn("skills_trace_candidate_submit", tools)

    def test_skills_list_mcp_http_parity(self) -> None:
        actor = self.local.verify(f"Bearer {self.token}")
        http_env = self.service.dispatch("skills_list", {}, actor=actor)
        mcp_env = self.mcp.call_tool(
            "skills_list",
            {"params": {}},
            authorization=f"Bearer {self.token}",
        )
        self.assertEqual(
            [s["skill_id"] for s in http_env["data"]["skills"]],
            [s["skill_id"] for s in mcp_env["data"]["skills"]],
        )
        self.assertEqual(http_env["data"]["count"], mcp_env["data"]["count"])

    def test_mcp_rejects_spoofed_actor_claims_in_args(self) -> None:
        with self.assertRaises(AuthError) as ctx:
            self.mcp.call_tool(
                "skills_list",
                {
                    "params": {},
                    "actor_id": "attacker",
                },
                authorization=f"Bearer {self.token}",
            )
        self.assertEqual(ctx.exception.code, "auth_spoof_rejected")

    def test_mcp_rejects_caller_minted_actor_claims(self) -> None:
        with self.assertRaises(AuthError) as ctx:
            self.mcp.call_tool(
                "skills_list",
                {
                    "params": {},
                    "actor_claims": {
                        "actor_id": "attacker",
                        "actor_kind": "service",
                        "org_id": "evil-org",
                        "scopes": ["skills:write"],
                        "exp": int(time.time()) + 3600,
                    },
                },
            )
        self.assertIn(ctx.exception.code, {"auth_claims_mint_forbidden", "auth_missing"})

    def test_mcp_rejects_actor_claims_without_authorization(self) -> None:
        response = self.mcp.handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {
                    "name": "skills_list",
                    "arguments": {"params": {}},
                    "_meta": {
                        "actor_claims": {
                            "actorId": "attacker",
                            "orgId": "evil",
                        }
                    },
                },
            }
        )
        assert response is not None
        self.assertIn("error", response)
        self.assertEqual(response["error"]["data"]["code"], "auth_missing")

    def test_jsonrpc_tools_call(self) -> None:
        response = self.mcp.handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "skills_list",
                    "arguments": {"params": {}},
                    "_meta": {"authorization": f"Bearer {self.token}"},
                },
            }
        )
        assert response is not None
        self.assertIn("result", response)
        structured = response["result"]["structuredContent"]
        self.assertGreater(structured["data"]["count"], 0)

    def test_injected_default_actor_allows_call(self) -> None:
        actor = self.local.verify(f"Bearer {self.token}")
        mcp = SkillsMcpServer(
            service=self.service,
            verifier=self.local,
            default_actor=actor,
        )
        env = mcp.call_tool("skills_list", {"params": {}})
        self.assertGreater(env["data"]["count"], 0)

    def test_default_construction_without_authenticator_fails_closed(self) -> None:
        # Production default path must not silently use unsigned decoding.
        import os

        old = os.environ.pop("LINKSKILLS_PLATFORM_AUTHENTICATOR", None)
        old_mode = os.environ.get("LINKSKILLS_AUTH_MODE")
        os.environ["LINKSKILLS_AUTH_MODE"] = "production"
        try:
            with self.assertRaises(AuthConfigurationError):
                SkillsMcpServer(service=self.service)
        finally:
            if old is not None:
                os.environ["LINKSKILLS_PLATFORM_AUTHENTICATOR"] = old
            if old_mode is None:
                os.environ.pop("LINKSKILLS_AUTH_MODE", None)
            else:
                os.environ["LINKSKILLS_AUTH_MODE"] = old_mode

    def test_canary_requires_platform_bearer(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_canary_default_actor(
                environ={
                    "LINKSKILLS_CANARY": "1",
                    "LINKSKILLS_AUTH_MODE": "production",
                }
            )

    def test_canary_rejects_local_test_mode(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            resolve_canary_default_actor(
                environ={
                    "LINKSKILLS_CANARY": "1",
                    "LINKSKILLS_AUTH_MODE": "local-test",
                    "LINKSKILLS_CANARY_AUTHORIZATION": f"Bearer {self.token}",
                }
            )
        self.assertIn("local-test", str(ctx.exception))

    def test_canary_accepts_signed_bearer_with_production_verifier(self) -> None:
        signed = mint_signed_test_bearer(_claims())
        verifier = production_test_verifier()
        actor = resolve_canary_default_actor(
            environ={
                "LINKSKILLS_CANARY": "1",
                "LINKSKILLS_AUTH_MODE": "production",
                "LINKSKILLS_CANARY_AUTHORIZATION": f"Bearer {signed}",
            },
            verifier=verifier,
        )
        assert actor is not None
        self.assertEqual(actor.actor_id, "actor-mcp")

    def test_canary_rejects_unsigned_bearer_even_if_injected(self) -> None:
        verifier = production_test_verifier()
        with self.assertRaises(AuthError) as ctx:
            resolve_canary_default_actor(
                environ={
                    "LINKSKILLS_CANARY": "1",
                    "LINKSKILLS_AUTH_MODE": "production",
                    "LINKSKILLS_CANARY_AUTHORIZATION": f"Bearer {self.token}",
                },
                verifier=verifier,
            )
        self.assertEqual(ctx.exception.code, "auth_unsigned_rejected")


if __name__ == "__main__":
    unittest.main()
