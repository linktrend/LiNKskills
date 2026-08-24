import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "sales-customer-management"


def load_helper():
    spec = importlib.util.spec_from_file_location("scm_helper", SKILL / "scripts" / "helper_tool.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SalesCustomerManagementContractTests(unittest.TestCase):
    def test_required_artifacts_and_boundaries(self):
        required = ["SKILL.md", "advanced/advanced.md", "references/schemas.json", "references/eval-suite.json", "references/eval-suite.yaml", "references/api-specs.md", "references/old-patterns.md", "scripts/helper_tool.py"]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ["Odoo", "LiNKreach", "PENDING_APPROVAL", "execution_ledger.jsonl", "state.jsonl", "native CLI", "CLI wrapper", "direct API", "MCP", "specialist", "generalist", "get_tool_details", "Other — specify"]:
            self.assertIn(phrase, body)
        for forbidden in ["send: true", "applied: true", "mutated_records: true", "sk_live_", "BEGIN PRIVATE KEY"]:
            self.assertNotIn(forbidden, body)

    def test_contract_schema_and_eval_cases(self):
        schema = json.loads((SKILL / "references/schemas.json").read_text(encoding="utf-8"))
        self.assertTrue({"input", "output", "state"}.issubset(schema["definitions"]))
        self.assertIn("source_evidence", schema["definitions"]["input"]["required"])
        self.assertIn("effects", schema["definitions"]["output"]["required"])
        suite = json.loads((SKILL / "references/eval-suite.json").read_text(encoding="utf-8"))
        self.assertEqual("sales-customer-management", suite["skill_id"])
        self.assertGreaterEqual(len(suite["cases"]), 10)
        text = json.dumps(suite)
        for unsafe in ["sk_live", "customer@example.com", "BEGIN PRIVATE KEY", "real account"]:
            self.assertNotIn(unsafe, text)

    def test_helper_is_deterministic_and_side_effect_free(self):
        helper = load_helper()
        request = {"workflow": "pipeline", "privacy_classification": "synthetic", "source_evidence": [{"ref": "fixture:lead-demo-001", "status": "confirmed"}]}
        first = helper.normalize_request(request)
        second = helper.normalize_request(request)
        self.assertEqual(first, second)
        self.assertEqual("PENDING_APPROVAL", first["status"])
        self.assertEqual({"sent": False, "applied": False, "mutated_records": False}, first["effects"])
        self.assertEqual("FAILED", helper.normalize_request({"privacy_classification": "restricted"})["status"])


if __name__ == "__main__":
    unittest.main()
