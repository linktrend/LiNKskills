#!/usr/bin/env python3
"""Focused v0.2 contract parity and negative-boundary tests."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from linkskills_contracts import load_schema, validate_instance  # noqa: E402


def load_fixture(*parts: str) -> dict:
    with ROOT.joinpath("fixtures", *parts).open(encoding="utf-8") as handle:
        return json.load(handle)


class V2ContractTests(unittest.TestCase):
    def assert_valid(self, payload: dict, schema: str) -> None:
        result = validate_instance(payload, schema)
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])

    def assert_invalid(self, payload: dict, schema: str) -> None:
        result = validate_instance(payload, schema)
        self.assertFalse(result.ok, msg="payload unexpectedly validated")

    def test_v2_schemas_load(self) -> None:
        for name in (
            "provider-metadata-v0.2.json",
            "mcp-policy-v0.2.json",
            "use-report-v0.2.json",
            "compatibility-evidence-v0.2.json",
        ):
            self.assertEqual(load_schema(name)["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_policy_map_and_legacy_inventory_have_expected_parity(self) -> None:
        policy = load_fixture("mcp", "v0.2-policy.json")
        legacy = load_fixture("mcp", "legacy-v0.1-compatibility.json")
        self.assertEqual(len(policy["operation_map"]["tools"]), 6)
        self.assertEqual(len(policy["operation_map"]["resources"]), 13)
        self.assertEqual(len(legacy["legacy_http"]["operations"]), 15)
        self.assertEqual(legacy["legacy_http"]["operations"], legacy["legacy_mcp"]["tools"])
        self.assertEqual(legacy["legacy_http"]["resources"], [])
        self.assertEqual(legacy["legacy_mcp"]["resources"], [])
        read_operations = {
            "skills_capabilities_get", "skills_catalog_list", "skills_catalog_search",
            "skills_release_list", "skills_release_describe", "skills_release_entrypoint_get",
            "skills_release_sections_list", "skills_release_section_get",
            "skills_release_resources_list", "skills_release_resource_get",
            "skills_release_content_get", "skills_release_package_get", "skills_qualification_get",
        }
        self.assertTrue(read_operations.isdisjoint(policy["operation_map"]["tools"]))
        self.assertEqual(
            set(policy["operation_map"]["tools"]),
            {"skills_release_verify", "skills_use_report_submit", "skills_use_report_status_get",
             "skills_feedback_submit", "skills_feedback_status_get", "skills_librarian_status_get"},
        )
        self.assertTrue(
            {"skills://guide/capabilities", "skills://catalog?cursor={cursor}&limit={limit}",
             "skills://catalog/search?query={query}&cursor={cursor}&limit={limit}",
             "skills://release/{skill_id}/{version}/manifest",
             "skills://release/{skill_id}/{version}/entrypoint",
             "skills://release/{skill_id}/{version}/section/{section_id}?cursor={cursor}&limit={limit}",
             "skills://release/{skill_id}/{version}/resource/{resource_id}?cursor={cursor}&limit={limit}"}
            .issubset(policy["operation_map"]["resources"])
        )
        self.assertNotIn("skills_tool_invoke", policy["operation_map"]["tools"])
        self.assertFalse(policy["compatibility_policy"]["no_dual_era_downgrade"] is False)
        self.assert_valid(policy, "mcp-policy-v0.2.json")
        self.assert_valid(legacy, "compatibility-evidence-v0.2.json")

    def test_metadata_vocabularies_and_informational_authority(self) -> None:
        payload = load_fixture("metadata", "valid-informational.json")
        self.assert_valid(payload, "provider-metadata-v0.2.json")
        self.assertEqual(payload["jurisdiction_or_venue"]["qualified_jurisdiction"], "TW")
        self.assertEqual(payload["format_compatibility"]["authoritative_format"], "skill_pack_v0.1")
        self.assertTrue(payload["authority"]["metadata_only"])

    def test_metadata_rejects_secret_private_and_authority_escalation_fields(self) -> None:
        base = load_fixture("metadata", "valid-informational.json")
        for field, value in (
            ("api_key", "do-not-store"),
            ("consumer", {"id": "private"}),
            ("lead", {"email": "private"}),
            ("trading_order", {"symbol": "private"}),
        ):
            payload = copy.deepcopy(base)
            payload[field] = value
            self.assert_invalid(payload, "provider-metadata-v0.2.json")

        payload = copy.deepcopy(base)
        payload["authority"]["can_execute"] = True
        self.assert_invalid(payload, "provider-metadata-v0.2.json")

        payload = copy.deepcopy(base)
        payload["scope_refs"] = ["plain:unbounded-consumer-id"]
        self.assert_invalid(payload, "provider-metadata-v0.2.json")

    def test_telemetry_variants(self) -> None:
        for name in ("completed-score-10.json", "completed-score-9.json", "non-use.json"):
            self.assert_valid(load_fixture("telemetry", name), "use-report-v0.2.json")

    def test_score_ten_bans_issue_and_score_nine_requires_typed_issue(self) -> None:
        score_ten = load_fixture("telemetry", "completed-score-10.json")
        score_ten["issue"] = {"type": "other", "severity": "low", "issue_ref": "opaque:issue:bad"}
        self.assert_invalid(score_ten, "use-report-v0.2.json")

        score_nine = load_fixture("telemetry", "completed-score-9.json")
        del score_nine["issue"]
        self.assert_invalid(score_nine, "use-report-v0.2.json")

    def test_telemetry_rejects_secrets_private_data_narratives_and_unbounded_fields(self) -> None:
        base = load_fixture("telemetry", "completed-score-10.json")
        for field, value in (
            ("authorization", "Bearer secret"),
            ("prompt", "private transcript"),
            ("case", {"id": "private"}),
            ("portfolio", {"positions": "private"}),
            ("narrative", "long free text"),
        ):
            payload = copy.deepcopy(base)
            payload[field] = value
            self.assert_invalid(payload, "use-report-v0.2.json")

        payload = copy.deepcopy(base)
        payload["opaque_refs"] = ["opaque:" + ("x" * 200)]
        self.assert_invalid(payload, "use-report-v0.2.json")

    def test_non_use_rejects_completed_use_fields(self) -> None:
        payload = load_fixture("telemetry", "non-use.json")
        payload["score"] = 0
        self.assert_invalid(payload, "use-report-v0.2.json")


if __name__ == "__main__":
    unittest.main()
