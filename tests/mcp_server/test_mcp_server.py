#!/usr/bin/env python3
"""MCP server tests — parity with gateway service for skills_list."""

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

from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402
from linkskills_mcp.server import SkillsMcpServer  # noqa: E402


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
        self.mcp = SkillsMcpServer(service=self.service)
        self.token = mint_test_bearer(_claims())

    def test_tools_list_includes_skills_operations(self) -> None:
        tools = {t["name"] for t in self.mcp.list_tools()}
        self.assertIn("skills_list", tools)
        self.assertIn("skills_run_start", tools)
        self.assertIn("skills_trace_candidate_submit", tools)

    def test_skills_list_mcp_http_parity(self) -> None:
        from linkskills_gateway.auth import PlatformClaimsVerifier

        actor = PlatformClaimsVerifier().verify(f"Bearer {self.token}")
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
        from linkskills_gateway.auth import AuthError

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


if __name__ == "__main__":
    unittest.main()
