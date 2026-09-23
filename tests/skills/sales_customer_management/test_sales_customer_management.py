import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "eval_runner"))
sys.path.insert(0, str(ROOT / "packages" / "core"))
sys.path.insert(0, str(ROOT / "packages" / "contracts"))

from linkskills_contracts import validate_instance  # noqa: E402
from linkskills_eval_runner.assertions import (  # noqa: E402
    assertions_hard_failed,
    assertions_passed,
    parse_assertion_spec,
    run_assertions,
)


SKILL = ROOT / "skills" / "sales-customer-management"


def load_helper():
    spec = importlib.util.spec_from_file_location("scm_helper", SKILL / "scripts" / "helper_tool.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SalesCustomerManagementContractTests(unittest.TestCase):
    def assert_output_contract(self, output):
        schema = json.loads((SKILL / "references/schemas.json").read_text(encoding="utf-8"))["definitions"]["output"]
        result = validate_instance(output, schema)
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])

    def test_required_artifacts_and_boundaries(self):
        required = ["SKILL.md", "advanced/advanced.md", "references/schemas.json", "references/eval-suite.json", "references/eval-suite.yaml", "references/api-specs.md", "references/old-patterns.md", "scripts/helper_tool.py"]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ["Odoo", "LiNKclient", "PENDING_APPROVAL", "execution_ledger.jsonl", "state.jsonl", "native CLI", "CLI wrapper", "direct API", "MCP", "specialist", "generalist", "get_tool_details", "Other — specify"]:
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

    def test_synthetic_qualification_assertions_match_helper(self):
        suite = yaml.safe_load((SKILL / "references/eval-suite.yaml").read_text(encoding="utf-8"))
        scenario = next(item for item in suite["scenarios"] if item["id"] == "synthetic-lead-qualification")
        proc = subprocess.run(
            [sys.executable, str(SKILL / "scripts/helper_tool.py"), *scenario["execute"]["argv"]],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "COMPLETED")
        self.assertEqual(payload["qualification"]["status"], "qualified")
        self.assertFalse(payload["effects"]["sent"])
        self.assertNotIn("permission_to_act", payload)
        results = run_assertions(
            proc.stdout,
            parse_assertion_spec(scenario["assertions"]),
            observed_exit_code=proc.returncode,
            workspace_root=SKILL,
        )
        self.assertTrue(assertions_passed(results), msg=[result.detail for result in results])
        self.assertFalse(assertions_hard_failed(results))

    def test_helper_is_deterministic_and_side_effect_free(self):
        helper = load_helper()
        request = {"workflow": "pipeline", "privacy_classification": "synthetic", "source_evidence": [{"ref": "fixture:lead-demo-001", "status": "confirmed"}]}
        first = helper.normalize_request(request)
        second = helper.normalize_request(request)
        self.assertEqual(first, second)
        self.assert_output_contract(first)
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
        privacy_result = helper.normalize_request(email)
        self.assert_output_contract(privacy_result)
        self.assertEqual("FAILED", privacy_result["status"])
        missing = {"workflow": "qualification", "privacy_classification": "synthetic", "source_evidence": []}
        missing_result = helper.normalize_request(missing)
        self.assert_output_contract(missing_result)
        self.assertEqual("FAILED", missing_result["status"])
        not_reported = {"workflow": "qualification", "privacy_classification": "synthetic", "source_evidence": [{"ref": "fixture:x", "status": "not_reported"}]}
        not_reported_result = helper.normalize_request(not_reported)
        self.assert_output_contract(not_reported_result)
        self.assertEqual("PENDING_APPROVAL", not_reported_result["status"])


if __name__ == "__main__":
    unittest.main()
