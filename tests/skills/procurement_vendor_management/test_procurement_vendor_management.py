import importlib.util
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "procurement-vendor-management"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))

from linkskills_contracts import validate_instance  # noqa: E402


def load_helper():
    spec = importlib.util.spec_from_file_location("pvm_helper", SKILL / "scripts" / "helper_tool.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ProcurementVendorManagementTests(unittest.TestCase):
    def output_check(self, output):
        schema = json.loads((SKILL / "references/schemas.json").read_text(encoding="utf-8"))["definitions"]["output"]
        result = validate_instance(output, schema)
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])

    def test_required_artifacts_and_boundaries(self):
        required = ["SKILL.md", "advanced/advanced.md", "references/schemas.json", "references/eval-suite.json", "references/eval-suite.yaml", "references/api-specs.md", "references/old-patterns.md", "scripts/helper_tool.py"]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ["supplier", "pricing", "renewal", "performance", "continuity", "approval", "PENDING_APPROVAL", "execution_ledger.jsonl", "state.jsonl", "native CLI", "CLI wrapper", "direct API", "MCP", "get_tool_details", "Other — specify"]:
            self.assertIn(phrase, body)
        for forbidden in ["ordered: true", "accepted: true", "sent: true", "mutated_records: true", "sk_live_", "BEGIN PRIVATE KEY"]:
            self.assertNotIn(forbidden, body)

    def test_schema_eval_and_source_review(self):
        schema = json.loads((SKILL / "references/schemas.json").read_text(encoding="utf-8"))
        self.assertTrue({"input", "output", "state"}.issubset(schema["definitions"]))
        self.assertIn("requested_actions", schema["definitions"]["input"]["properties"])
        self.assertIn("rollback", schema["definitions"]["output"]["required"])
        self.assertEqual(schema["definitions"]["output"]["properties"]["rollback"]["const"], "ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/tree:9d0be7cedb0fc4ec42bf382735ede36d100f8614")
        api = (SKILL / "references/api-specs.md").read_text(encoding="utf-8")
        for phrase in ("Existing-overlap and source review matrix", "Licence/provenance review", "Security/privacy review", "Maintenance review", "Official Odoo external API documentation", "ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/tree:9d0be7cedb0fc4ec42bf382735ede36d100f8614"):
            self.assertIn(phrase, api)
        suite = json.loads((SKILL / "references/eval-suite.json").read_text(encoding="utf-8"))
        self.assertEqual("procurement-vendor-management", suite["skill_id"])
        self.assertGreaterEqual(len(suite["cases"]), 10)
        self.assertNotIn("live credentials", json.dumps(suite).lower())

    def test_helper_is_deterministic_and_effect_free(self):
        helper = load_helper()
        request = {"workflow": "supplier_comparison", "privacy_classification": "synthetic", "source_evidence": [{"ref": "fixture:supplier-demo-001", "claim": "synthetic comparison", "status": "confirmed", "provenance": "owner-fixture", "licence": "internal"}]}
        first = helper.normalize_request(request)
        self.assertEqual(first, helper.normalize_request(request))
        self.output_check(first)
        self.assertEqual("COMPLETED", first["status"])
        self.assertEqual({"sent": False, "accepted": False, "ordered": False, "mutated_records": False}, first["effects"])
        self.assertEqual(first["disposition"], first["decision"]["disposition"])
        self.assertRegex(first["idempotency_key"], r"^pvm-[a-f0-9]{16}$")

    def test_helper_rejects_privacy_missing_evidence_and_unknown_actions(self):
        helper = load_helper()
        base = {"workflow": "supplier_intake", "privacy_classification": "synthetic", "source_evidence": [{"ref": "fixture:supplier-demo-002", "claim": "synthetic", "status": "confirmed", "provenance": "fixture", "licence": "internal"}]}
        privacy = helper.normalize_request({**base, "privacy_classification": "restricted"})
        missing = helper.normalize_request({**base, "source_evidence": []})
        unknown = helper.normalize_request({**base, "requested_actions": ["publish"]})
        for result in (privacy, missing, unknown):
            self.output_check(result)
            self.assertEqual(helper.ROLLBACK_TARGET, result["rollback"])
        self.assertEqual("FAILED", privacy["status"])
        self.assertEqual("FAILED", missing["status"])
        self.assertEqual("PENDING_APPROVAL", unknown["status"])
        self.assertEqual("authority_escalation", unknown["disposition"])

    def test_effectful_and_malformed_actions_fail_closed(self):
        helper = load_helper()
        request = {"workflow": "approval_brief", "privacy_classification": "synthetic", "source_evidence": [{"ref": "fixture:supplier-demo-003", "status": "confirmed"}]}
        for actions in (["order"], ["accept", "send"], ["read", "publish"], "prepare"):
            result = helper.normalize_request({**request, "requested_actions": actions})
            self.output_check(result)
            self.assertEqual("PENDING_APPROVAL", result["status"])
            self.assertTrue(result["escalation"]["required"])
            self.assertTrue(all(value is False for value in result["effects"].values()))

    def test_eval_suite_has_all_procurement_workflows(self):
        suite = json.loads((SKILL / "references/eval-suite.json").read_text(encoding="utf-8"))
        text = json.dumps(suite)
        for phrase in ("supplier-comparison", "pricing-conflict", "renewal-review", "performance-review", "continuity-risk", "approval-brief", "authority-denial", "tool-failure"):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
