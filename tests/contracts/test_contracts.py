#!/usr/bin/env python3
"""Contract schema fixture and validator tests."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_ROOT = REPO_ROOT / "packages" / "contracts"
sys.path.insert(0, str(CONTRACTS_ROOT))

from linkskills_contracts import list_schemas, load_schema, validate_instance  # noqa: E402


class SchemaPresenceTests(unittest.TestCase):
    EXPECTED = {
        "skill-pack-v0.1.json",
        "skill-fragment-v0.1.json",
        "dependency-types-v0.1.json",
        "tool-descriptor-v0.1.json",
        "runtime-profile-v0.1.json",
        "execution-profile-v0.1.json",
        "eval-suite-v0.1.json",
        "run-event-v0.1.json",
        "feedback-v0.1.json",
        "release-record-v0.1.json",
        "error-envelope-v0.1.json",
        "mcp-api-envelope-v0.1.json",
    }

    def test_all_v01_schemas_present(self) -> None:
        names = set(list_schemas())
        self.assertTrue(self.EXPECTED.issubset(names), msg=sorted(self.EXPECTED - names))

    def test_schemas_load(self) -> None:
        for name in sorted(self.EXPECTED):
            schema = load_schema(name)
            self.assertEqual(schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema")
            self.assertIn("properties", schema)


class FixtureValidationTests(unittest.TestCase):
    def _load(self, *parts: str) -> dict:
        path = CONTRACTS_ROOT.joinpath(*parts)
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_valid_skill_pack(self) -> None:
        payload = self._load("fixtures", "skill-pack", "valid-minimal.json")
        result = validate_instance(payload, "skill-pack")
        self.assertTrue(result.ok, msg=[str(e) for e in result.errors])

    def test_invalid_skill_pack_missing_telemetry(self) -> None:
        payload = self._load("fixtures", "skill-pack", "invalid-missing-telemetry.json")
        result = validate_instance(payload, "skill-pack")
        self.assertFalse(result.ok)
        self.assertTrue(any("telemetry" in e.path for e in result.errors))

    def test_valid_eval_suite(self) -> None:
        payload = self._load("fixtures", "eval-suite", "valid-minimal.json")
        result = validate_instance(payload, "eval-suite")
        self.assertTrue(result.ok, msg=[str(e) for e in result.errors])

    def test_invalid_eval_suite_empty_cases(self) -> None:
        payload = self._load("fixtures", "eval-suite", "invalid-empty-cases.json")
        result = validate_instance(payload, "eval-suite")
        self.assertFalse(result.ok)
        joined = " ".join(str(e) for e in result.errors)
        self.assertTrue("cases" in joined or "evidence_policy" in joined)


if __name__ == "__main__":
    unittest.main()
