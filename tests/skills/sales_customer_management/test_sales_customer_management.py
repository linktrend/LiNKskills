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
        api_specs = (SKILL / "references/api-specs.md").read_text(encoding="utf-8")
        for phrase in ("Existing-overlap and source review matrix", "Licence/provenance review", "Security/privacy review", "Maintenance review", "ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/tree:9d0be7cedb0fc4ec42bf382735ede36d100f8614"):
            self.assertIn(phrase, api_specs)
        example = (SKILL / "examples/success-pattern.md").read_text(encoding="utf-8")
        self.assertIn("never completes with", example)
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
        self.assertRegex(first["rollback"], r"^ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/")
        self.assertEqual("FAILED", helper.normalize_request({"privacy_classification": "restricted"})["status"])

    def test_task_id_uses_repository_global_runtime_format(self):
        task_id = "20260824-1537-SCM-000001"
        self.assertRegex(task_id, r"^\d{8}-\d{4}-[A-Z0-9]+-\d{6}$")
        self.assertNotRegex("scm-scm-demo-001-deadbeef", r"^\d{8}-\d{4}-[A-Z0-9]+-\d{6}$")
        schema = json.loads((SKILL / "references/schemas.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["definitions"]["state"]["properties"]["task_id"]["pattern"], r"^\d{8}-\d{4}-[A-Z0-9]+-\d{6}$")

    def test_helper_rejects_pii_and_missing_evidence(self):
        helper = load_helper()
        email = {"workflow": "qualification", "privacy_classification": "synthetic", "source_evidence": [{"ref": "fixture:x", "claim": "customer@example.com", "status": "confirmed"}]}
        self.assertEqual("FAILED", helper.normalize_request(email)["status"])
        missing = {"workflow": "qualification", "privacy_classification": "synthetic", "source_evidence": []}
        self.assertEqual("FAILED", helper.normalize_request(missing)["status"])
        not_reported = {"workflow": "qualification", "privacy_classification": "synthetic", "source_evidence": [{"ref": "fixture:x", "status": "not_reported"}]}
        self.assertEqual("PENDING_APPROVAL", helper.normalize_request(not_reported)["status"])


if __name__ == "__main__":
    unittest.main()
