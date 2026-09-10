#!/usr/bin/env python3
"""Acceptance-path coverage for production OpenAPI and MCP capability records."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "packages" / "contracts"
sys.path.insert(0, str(CONTRACTS))
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "gateway"))

from linkskills_contracts import validate_instance  # noqa: E402


class ProductionContractRecordsTests(unittest.TestCase):
    def test_openapi_and_capability_records(self) -> None:
        openapi = json.loads(
            (CONTRACTS / "fixtures" / "openapi" / "skills-api-v0.2.json").read_text(encoding="utf-8")
        )
        capabilities = json.loads(
            (CONTRACTS / "fixtures" / "mcp" / "v0.2-capabilities.json").read_text(encoding="utf-8")
        )
        self.assertEqual(openapi["info"]["version"], "skills.api.v0.2")
        self.assertIn("/v2/{operation}", openapi["paths"])
        self.assertEqual(capabilities["mcp_protocol"], "2026-07-28")
        self.assertFalse(capabilities["legacy_execution"])
        self.assertIsInstance(capabilities["resources"], list)
        self.assertIsInstance(capabilities["tools"], list)
        self.assertEqual(len(capabilities["resources"]), 13)
        self.assertEqual(len(capabilities["tools"]), 6)
        self.assertEqual(capabilities["initialize_protocol_version"], "2026-07-28")
        self.assertIn("/v2/mcp-capabilities", openapi["paths"])

    def test_live_capability_projection_matches_fixture(self) -> None:
        from linkskills_core.provider_v2 import V2Provider
        from linkskills_gateway.v2_http import capability_record

        live = capability_record(V2Provider(lambda token: None))
        fixture = json.loads(
            (CONTRACTS / "fixtures" / "mcp" / "v0.2-capabilities.json").read_text(encoding="utf-8")
        )
        runtime_only = {"catalog_ready"}
        for key, value in fixture.items():
            self.assertIn(key, live)
            if key in runtime_only:
                continue
            self.assertEqual(live[key], value, msg=key)
        self.assertIsInstance(live["catalog_ready"], bool)
        self.assertEqual(live["serverInfo"]["name"], "linkskills-mcp-v2")
        self.assertEqual(live["typed_errors"], fixture["typed_errors"])

    def test_legacy_compatibility_fixture_still_valid(self) -> None:
        legacy = json.loads(
            (CONTRACTS / "fixtures" / "mcp" / "legacy-v0.1-compatibility.json").read_text(encoding="utf-8")
        )
        result = validate_instance(legacy, "compatibility-evidence-v0.2.json")
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])
        self.assertEqual(len(legacy["legacy_http"]["operations"]), 15)

    def test_recorded_fixture_digests(self) -> None:
        import hashlib

        recorded = {
            "fixtures/mcp/v0.2-policy.json": "sha256:6f40f45382941ef23ce9e58b9facb95abdeaf32db88c539c2b33c521b24b7455",
            "fixtures/mcp/v0.2-capabilities.json": "sha256:ce76d7f2b2674aa85cc9ade510f5297bfb09d2f84fbc4de651abd2324dc39a03",
            "fixtures/openapi/skills-api-v0.2.json": "sha256:f623fec39c5c3ebc95a26e820295c0c60499fae2cba77c077adda507ba1e9fd3",
        }
        actual = {
            name: "sha256:" + hashlib.sha256((CONTRACTS / name).read_bytes()).hexdigest()
            for name in recorded
        }
        self.assertEqual(actual, recorded)


if __name__ == "__main__":
    unittest.main()
