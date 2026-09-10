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

    def test_legacy_compatibility_fixture_still_valid(self) -> None:
        legacy = json.loads(
            (CONTRACTS / "fixtures" / "mcp" / "legacy-v0.1-compatibility.json").read_text(encoding="utf-8")
        )
        result = validate_instance(legacy, "compatibility-evidence-v0.2.json")
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])
        self.assertEqual(len(legacy["legacy_http"]["operations"]), 15)


if __name__ == "__main__":
    unittest.main()
