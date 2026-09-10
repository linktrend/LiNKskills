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
            "fixtures/mcp/v0.2-capabilities.json": "sha256:4a433830c2b18074a838983046791a4fb12c65fed42dc9557f283aa3184b51b5",
            "fixtures/openapi/skills-api-v0.2.json": "sha256:d0f69b7eec643dfad2fb19158f2d63b47e1a475f8d92f833838fcf422a384e74",
        }
        actual = {
            name: "sha256:" + hashlib.sha256((CONTRACTS / name).read_bytes()).hexdigest()
            for name in recorded
        }
        self.assertEqual(actual, recorded)


if __name__ == "__main__":
    unittest.main()
