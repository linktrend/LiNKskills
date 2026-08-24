import importlib.util
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "commercial-contracts-legal-operations"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))

from linkskills_contracts import validate_instance  # noqa: E402


def load_helper():
    spec = importlib.util.spec_from_file_location("clo_helper", SKILL / "scripts" / "helper_tool.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CommercialContractsLegalOperationsTests(unittest.TestCase):
    def test_required_artifacts_and_legal_boundaries(self):
        required = ["SKILL.md", "advanced/advanced.md", "references/schemas.json", "references/eval-suite.json", "references/eval-suite.yaml", "references/api-specs.md", "references/old-patterns.md", "scripts/helper_tool.py"]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ["jurisdiction", "plain-English", "obligation", "renewal", "approved-playbook", "lawyer", "Principal", "PENDING_APPROVAL", "legal authority", "Other — specify", "execution_ledger.jsonl", "state.jsonl", "native CLI", "CLI wrapper", "direct API", "MCP", "specialist", "generalist", "get_tool_details"]:
            self.assertIn(phrase, body)
        for forbidden in ["signed: true", "accepted: true", "sent: true", "filed: true", "mutated_records: true", "sk_live_", "BEGIN PRIVATE KEY", "customer@example.com"]:
            self.assertNotIn(forbidden, body)

    def test_contract_schema_and_eval_suite(self):
        schema = json.loads((SKILL / "references/schemas.json").read_text(encoding="utf-8"))
        self.assertTrue({"input", "output", "state"}.issubset(schema["definitions"]))
        self.assertIn("matter_ref", schema["definitions"]["input"]["required"])
        self.assertIn("jurisdiction_assessment", schema["definitions"]["output"]["required"])
        self.assertIn("disposition", schema["definitions"]["output"]["required"])
        self.assertIn("idempotency_key", schema["definitions"]["output"]["required"])
        self.assertIn("legal_authority", schema["definitions"]["output"]["properties"]["decision"]["required"])
        suite = json.loads((SKILL / "references/eval-suite.json").read_text(encoding="utf-8"))
        self.assertEqual("commercial-contracts-legal-operations", suite["skill_id"])
        self.assertGreaterEqual(len(suite["cases"]), 10)
        text = json.dumps(suite)
        for unsafe in ["live contract text", "customer@example.com", "BEGIN PRIVATE KEY", "real contract"]:
            self.assertNotIn(unsafe, text)

    def test_helper_is_deterministic_and_refuses_authority(self):
        helper = load_helper()
        request = {"workflow": "obligation_register", "matter_ref": "matter-demo-001", "jurisdiction": "unknown", "privacy_classification": "synthetic", "source_evidence": [{"ref": "fixture:source-demo-001", "status": "confirmed"}]}
        first = helper.normalize_request(request)
        self.assertEqual(first, helper.normalize_request(request))
        self.assertEqual("PENDING_APPROVAL", first["status"])
        self.assertEqual({"sent": False, "signed": False, "accepted": False, "filed": False, "mutated_records": False}, first["effects"])
        blocked = helper.normalize_request({**request, "requested_actions": ["sign"]})
        self.assertEqual("authority_escalation", blocked["disposition"])
        self.assertEqual("FAILED", helper.normalize_request({**request, "privacy_classification": "restricted"})["status"])

    def test_helper_outputs_are_schema_complete_and_unknown_actions_fail_closed(self):
        helper = load_helper()
        output_schema = json.loads((SKILL / "references/schemas.json").read_text(encoding="utf-8"))["definitions"]["output"]
        base = {
            "workflow": "obligation_register",
            "matter_ref": "matter-demo-001",
            "jurisdiction": "Taiwan",
            "privacy_classification": "synthetic",
            "source_evidence": [{"ref": "fixture:source-demo-001", "status": "confirmed"}],
        }
        cases = [
            helper.normalize_request(base),
            helper.normalize_request({**base, "requested_actions": ["publish"]}),
            helper.normalize_request({**base, "privacy_classification": "restricted"}),
            helper.normalize_request({**base, "source_evidence": []}),
        ]
        for result in cases:
            checked = validate_instance(result, output_schema)
            self.assertTrue(checked.ok, msg=[str(error) for error in checked.errors])
            self.assertEqual(helper.ROLLBACK_TARGET, result["rollback"])
            self.assertEqual("not_granted", result["decision"]["legal_authority"])
            self.assertEqual(result["disposition"], result["decision"]["disposition"])
            self.assertRegex(result["idempotency_key"], r"^clo-[a-f0-9]{16}$")
            self.assertTrue(all(value is False for value in result["effects"].values()))
        unknown = cases[1]
        self.assertEqual("PENDING_APPROVAL", unknown["status"])
        self.assertEqual("authority_escalation", unknown["disposition"])
        self.assertTrue(unknown["escalation"]["required"])

    def test_helper_rejects_malformed_action_lists(self):
        helper = load_helper()
        request = {
            "workflow": "intake",
            "matter_ref": "matter-demo-001",
            "jurisdiction": "Taiwan",
            "privacy_classification": "synthetic",
            "source_evidence": [{"ref": "fixture:source-demo-001", "status": "confirmed"}],
        }
        for actions in ("prepare", ["read", 7], ["read", "publish"]):
            result = helper.normalize_request({**request, "requested_actions": actions})
            self.assertEqual("PENDING_APPROVAL", result["status"])
            self.assertEqual("authority_escalation", result["disposition"])

    def test_source_review_and_exact_rollback_evidence_are_named(self):
        text = (SKILL / "references/api-specs.md").read_text(encoding="utf-8")
        for phrase in (
            "Existing-overlap and source review matrix",
            "Anthropic Commercial Terms of Service",
            "Anthropic Privacy Policy",
            "Anthropic Consumer Terms",
            "ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/tree:9d0be7cedb0fc4ec42bf382735ede36d100f8614",
            "no prior qualified PKT-17 release",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
