#!/usr/bin/env python3
"""Production Cursor canary fragment must pin durable HTTP Gateway upstream."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAGMENT = REPO_ROOT / "configs" / "fragments" / "cursor-skills-canary.mcp.json.example"


class CursorCanaryFragmentDurablePathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(FRAGMENT.is_file(), f"missing fragment: {FRAGMENT}")
        self.doc = json.loads(FRAGMENT.read_text(encoding="utf-8"))
        servers = self.doc["mcpServers"]
        self.canary = servers["linkskills-canary"]
        self.env = self.canary["env"]

    def test_entrypoint_is_paci_stdio_proxy(self) -> None:
        self.assertEqual(self.canary["command"], "python3")
        self.assertEqual(
            self.canary["args"],
            ["-m", "linkskills_mcp.paci_stdio_proxy"],
        )

    def test_production_canary_uses_http_upstream(self) -> None:
        self.assertEqual(self.env["LINKSKILLS_AUTH_MODE"], "production")
        self.assertEqual(self.env["LINKSKILLS_CANARY"], "1")
        self.assertEqual(self.env["LINKSKILLS_MCP_UPSTREAM"], "http")

    def test_gateway_url_is_https_placeholder(self) -> None:
        url = self.env["GATEWAY_URL"]
        self.assertTrue(
            url.startswith("https://"),
            f"production canary GATEWAY_URL must be https, got {url!r}",
        )

    def test_fragment_does_not_enable_silent_inprocess_production(self) -> None:
        self.assertNotEqual(self.env.get("LINKSKILLS_MCP_UPSTREAM"), "in-process")
        self.assertNotIn("LINKSKILLS_MCP_ALLOW_INPROCESS_PRODUCTION", self.env)
        # No local-memory store knobs on the production canary profile.
        self.assertNotIn("LINKSKILLS_GATEWAY_STORE", self.env)
        self.assertNotEqual(self.env.get("LINKSKILLS_ENV", "").lower(), "local")

    def test_local_test_block_remains_explicit(self) -> None:
        local = self.doc["_local_test_static_bearer_only"]
        self.assertEqual(local["LINKSKILLS_AUTH_MODE"], "local-test")
        self.assertIn("LINKSKILLS_LOCAL_TEST_STATIC_BEARER", local)
        self.assertTrue(str(local["GATEWAY_URL"]).startswith("http://127.0.0.1"))

    def test_comment_honesty_and_telemetry_pointer(self) -> None:
        comment = self.doc["_comment"]
        self.assertIn("live_canary=false", comment)
        self.assertIn("global_cursor_mutation=false", comment)
        self.assertIn("TELEMETRY-CONTRACT.md", comment)
        self.assertIn("project-scoped disable", comment.lower())
        self.assertIn("~/.cursor/mcp.json", comment)
        self.assertIn("421a35e97bc302be0f5e1f196d0a5e8d132f6fd8", comment)
        self.assertIn("platform.auth-token-envelope/0.1.0", comment)
        self.assertIn("NOT 0.1.3-draft", comment)


if __name__ == "__main__":
    unittest.main()
