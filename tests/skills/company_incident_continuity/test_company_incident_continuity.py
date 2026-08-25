from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "company-incident-continuity"
REFS = SKILL / "references"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))
sys.path.insert(0, str(ROOT / "packages" / "core"))
from linkskills_contracts import validate_instance  # noqa: E402
from linkskills_core.hashing import verify_execution_profile_hashes  # noqa: E402


def load_helper():
    spec = importlib.util.spec_from_file_location("company_incident_helper", SKILL / "scripts" / "helper_tool.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request(**overrides):
    base = {
        "mode": "outage_review",
        "privacy_classification": "synthetic",
        "incident_ref": "incident:checkout-outage-001",
        "incident_type": "outage",
        "severity": "high",
        "state": "recovering",
        "owner": {"responder_ref": "owner:incident-lead", "platform_ref": "owner:platform", "program_ledger_ref": "consumer:program-ledger", "deployment_authority_ref": "owner:release"},
        "source_evidence": [{"ref": "fixture:incident-001", "status": "confirmed"}],
        "impacts": [{"id": "impact:checkout", "scope": "Synthetic checkout availability", "status": "observed", "evidence_ref": "fixture:incident-001"}],
        "recovery_options": [{"id": "recovery:restore", "label": "Restore from tested backup", "tradeoff": "Faster recovery; requires restore evidence.", "status": "proposed", "evidence_ref": "fixture:incident-001"}, {"id": "recovery:other", "label": "Other — specify", "tradeoff": "Owner may specify another bounded option.", "status": "proposed", "evidence_ref": "fixture:incident-001"}],
        "communications": [{"id": "communication:internal", "audience": "internal", "status": "draft", "summary": "Synthetic outage update for owner review.", "evidence_ref": "fixture:incident-001"}, {"id": "communication:customer", "audience": "customer", "status": "unsent", "summary": "Synthetic service update draft.", "evidence_ref": "fixture:incident-001"}],
    }
    base.update(overrides)
    return base


class CompanyIncidentContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = load_helper()
        cls.schemas = json.loads((REFS / "schemas.json").read_text(encoding="utf-8"))["definitions"]

    def assert_output_valid(self, output):
        schema = dict(self.schemas["output"])
        schema["definitions"] = self.schemas
        result = validate_instance(output, schema)
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])

    def test_required_artifacts_and_packet_terms(self):
        required = [
            "SKILL.md", "advanced/advanced.md", "examples/success-pattern.md", "examples/error-recovery.md",
            "references/api-specs.md", "references/changelog.md", "references/eval-suite.json", "references/eval-suite.yaml",
            "references/execution-profile.json", "references/old-patterns.md", "references/schemas.json", "references/skill-pack.json",
            "scripts/README.md", "scripts/helper_tool.py",
        ]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        for marker in ("outage", "security", "backup", "recovery", "continuity", "internal", "customer", "evidence", "closure", "responder", "platform", "program ledger", "deployment", "state.jsonl"):
            self.assertIn(marker, text, marker)

    def test_profile_and_eval_hashes_are_canonical(self):
        self.assertEqual(verify_execution_profile_hashes(SKILL), [])
        profile = json.loads((REFS / "execution-profile.json").read_text(encoding="utf-8"))
        suite_bytes = (REFS / "eval-suite.json").read_bytes()
        self.assertEqual(profile["eval_suite_hash"], "sha256:" + hashlib.sha256(suite_bytes).hexdigest())
        suite = json.loads(suite_bytes)
        self.assertEqual(suite["skill_id"], "company-incident-continuity")
        self.assertEqual(len(suite["cases"]), 9)

    def test_valid_outage_review_preserves_owners_impacts_and_draft_messages(self):
        result = self.helper.normalize_request(request())
        self.assertEqual(result["status"], "READY_FOR_OWNER")
        self.assertEqual(result["owner"]["platform_ref"], "owner:platform")
        self.assertEqual(result["impacts"][0]["status"], "observed")
        self.assertFalse(any(row["sent"] for row in result["communications"]))
        self.assertEqual(result["effects"], {"messages_sent": [], "external_calls": [], "mutations": []})
        self.assert_output_valid(result)

    def test_security_and_continuity_modes_keep_unknowns_honest(self):
        evidence = [{"ref": "fixture:incident-001", "status": "not_reported"}]
        for mode, incident_type in (("security_coordination", "security"), ("continuity_review", "continuity")):
            result = self.helper.normalize_request(request(mode=mode, incident_type=incident_type, source_evidence=evidence))
            self.assertEqual(result["status"], "DRAFT")
            self.assertTrue(result["uncertainty"])
            self.assert_output_valid(result)

    def test_recovery_and_closure_require_evidence_without_activation(self):
        closure = {"status": "proposed", "evidence_refs": ["fixture:incident-001"], "residual_risks": ["Restore timing remains owner-confirmed."], "owner_ref": "owner:incident-lead"}
        result = self.helper.normalize_request(request(mode="closure_review", closure=closure))
        self.assertEqual(result["closure"]["status"], "PROPOSED")
        self.assertFalse(result["closure"]["activated"])
        self.assertFalse(result["ownership"]["deployment_mutated"])
        self.assert_output_valid(result)
        missing = self.helper.normalize_request(request(mode="closure_review", closure={"status": "proposed", "evidence_refs": []}))
        self.assertEqual(missing["status"], "BLOCKED")

    def test_authority_privacy_and_duplicate_boundaries_fail_closed(self):
        for action in ("deploy", "rollback", "isolate", "rotate_credentials", "send", "approve", "close", "mutate_program"):
            result = self.helper.normalize_request(request(requested_action=action))
            self.assertEqual(result["status"], "BLOCKED", action)
            self.assert_output_valid(result)
        private = self.helper.normalize_request(request(communications=[{"id": "communication:private", "audience": "internal", "status": "draft", "summary": "confidential incident text", "evidence_ref": "fixture:incident-001"}]))
        self.assertEqual(private["status"], "BLOCKED")
        self.assertNotIn("confidential incident text", json.dumps(private))
        duplicate = request(source_evidence=[{"ref": "fixture:incident-001", "status": "confirmed"}, {"ref": "fixture:incident-001", "status": "confirmed"}])
        self.assertEqual(self.helper.normalize_request(duplicate)["status"], "BLOCKED")

    def test_schema_rejects_mutation_and_valid_result(self):
        result = self.helper.normalize_request(request())
        self.assert_output_valid(result)
        unsafe = deepcopy(result)
        unsafe["ownership"]["deployment_mutated"] = True
        schema = dict(self.schemas["output"])
        schema["definitions"] = self.schemas
        self.assertFalse(validate_instance(unsafe, schema).ok)

    def test_unknown_impact_and_option_state_fail_closed(self):
        bad_impact = request(impacts=[{"id": "impact:x", "scope": "scope", "status": "inferred", "evidence_ref": "fixture:incident-001"}])
        self.assertEqual(self.helper.normalize_request(bad_impact)["status"], "BLOCKED")
        bad_option = request(recovery_options=[{"id": "recovery:x", "label": "One", "tradeoff": "Unknown", "status": "approved", "evidence_ref": "fixture:incident-001"}])
        self.assertEqual(self.helper.normalize_request(bad_option)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
