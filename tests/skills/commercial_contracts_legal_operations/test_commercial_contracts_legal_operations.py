import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "commercial-contracts-legal-operations"


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


if __name__ == "__main__":
    unittest.main()
