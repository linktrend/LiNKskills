from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "agent-workforce-management"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))
sys.path.insert(0, str(ROOT / "packages" / "core"))

from linkskills_contracts import validate_instance  # noqa: E402
from linkskills_core.hashing import verify_execution_profile_hashes  # noqa: E402


def load_helper():
    """Load the owned deterministic helper without installing the skill."""
    spec = importlib.util.spec_from_file_location("agent_workforce_helper", SKILL / "scripts" / "helper_tool.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AgentWorkforceManagementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = json.loads((SKILL / "references" / "schemas.json").read_text(encoding="utf-8"))["definitions"]

    def evidence(self, status="confirmed"):
        return [{"ref": "fixture:workforce-pkt20-001", "status": status}]

    def request(self, mode="workforce_review", **extra):
        request = {
            "mode": mode,
            "privacy_classification": "synthetic",
            "workforce_ref": "workforce:quarterly-review-001",
            "source_evidence": self.evidence(),
            "role": {"role_ref": "role:research-lead", "purpose": "Coordinate public research triage.", "domain": "research", "boundary": "May prepare evidence summaries; may not grant tools or activate agents.", "owner_ref": "owner:principal", "evidence_ref": "fixture:workforce-pkt20-001"},
            "rule_selection": {"rule_ref": "rule:research-quality-v1", "applicability": "applicable", "evidence_ref": "fixture:workforce-pkt20-001"},
            "capability_requests": [{"capability_ref": "capability:research-read", "purpose": "Read supplied public research sources.", "evidence_ref": "fixture:workforce-pkt20-001"}],
            "delegations": [{"delegation_ref": "delegation:research-triage", "domain": "research", "owner_ref": "owner:principal", "status": "proposed", "evidence_ref": "fixture:workforce-pkt20-001"}],
            "workload": [{"agent_ref": "agent:research-001", "load_state": "balanced", "blocker_refs": [], "evidence_ref": "fixture:workforce-pkt20-001"}],
            "quality": [{"agent_ref": "agent:research-001", "outcome": "passed", "repeated_failure_count": 0, "evidence_ref": "fixture:workforce-pkt20-001"}],
            "proposals": [{"proposal_ref": "proposal:research-training", "agent_ref": "agent:research-001", "kind": "training", "status": "proposed", "reason": "Review citation refresher training.", "evidence_ref": "fixture:workforce-pkt20-001"}],
            "recommendation": "Keep the role owner-reviewed and schedule a citation refresher review.",
        }
        request.update(extra)
        return request

    def assert_valid_output(self, output):
        schema = dict(self.schemas["output"])
        schema["definitions"] = self.schemas
        result = validate_instance(output, schema)
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])

    def test_required_artifacts_and_scope_surface(self):
        required = [
            "SKILL.md", "advanced/advanced.md", "examples/success-pattern.md", "examples/error-recovery.md",
            "references/api-specs.md", "references/changelog.md", "references/eval-suite.json", "references/eval-suite.yaml",
            "references/execution-profile.json", "references/old-patterns.md", "references/schemas.json", "references/skill-pack.json",
            "scripts/README.md", "scripts/helper_tool.py",
        ]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        for marker in ("reusable role", "brain", "capability", "delegation", "workload", "blocker", "quality", "repeated failure", "suspend", "retire", "credentials", "private memory", "authority"):
            self.assertIn(marker, content)
        self.assertNotIn("catalog/index.json", content)

    def test_role_rule_capability_delegation_are_owner_ready_and_effect_free(self):
        result = load_helper().normalize_request(self.request(mode="delegation_plan"))
        self.assertEqual(result["status"], "READY_FOR_OWNER")
        self.assert_valid_output(result)
        self.assertEqual(result["authority"]["grants_approved"], False)
        self.assertEqual(result["effects"], {"messages_sent": [], "external_calls": [], "mutations": []})

    def test_uncertain_evidence_and_rule_stay_draft(self):
        request = self.request(source_evidence=self.evidence("not_reported"), mode="rule_selection")
        request["rule_selection"]["applicability"] = "uncertain"
        result = load_helper().normalize_request(request)
        self.assertEqual(result["status"], "DRAFT")
        self.assertTrue(result["uncertainty"])
        self.assert_valid_output(result)

    def test_workload_blockers_and_quality_failures_remain_observations(self):
        request = self.request(mode="quality_review", quality=[{"agent_ref": "agent:research-001", "outcome": "failed", "repeated_failure_count": 3, "evidence_ref": "fixture:workforce-pkt20-001"}], workload=[{"agent_ref": "agent:research-001", "load_state": "blocked", "blocker_refs": ["fixture:workforce-pkt20-001"], "evidence_ref": "fixture:workforce-pkt20-001"}])
        result = load_helper().normalize_request(request)
        self.assertEqual(result["status"], "READY_FOR_OWNER")
        self.assertEqual(result["quality"][0]["repeated_failure_count"], 3)
        self.assertEqual(result["authority"]["agents_suspended"], False)
        self.assert_valid_output(result)

    def test_suspend_and_retire_are_proposals_only(self):
        proposal = {"proposal_ref": "proposal:suspend-review", "agent_ref": "agent:research-001", "kind": "suspend", "status": "proposed", "reason": "Owner review after repeated failures.", "evidence_ref": "fixture:workforce-pkt20-001"}
        result = load_helper().normalize_request(self.request(mode="suspend_proposal", proposals=[proposal]))
        self.assertEqual(result["status"], "READY_FOR_OWNER")
        self.assertEqual(result["proposals"][0]["status"], "proposed")
        self.assertFalse(result["authority"]["agents_suspended"])
        self.assert_valid_output(result)

    def test_authority_actions_fail_closed(self):
        helper = load_helper()
        for action in ("activate", "suspend", "retire", "approve_grant", "copy_credentials", "copy_private_memory", "unknown"):
            result = helper.normalize_request(self.request(requested_action=action))
            self.assertEqual(result["status"], "BLOCKED", action)
            self.assertEqual(result["capability_requests"], [])
            self.assert_valid_output(result)

    def test_private_memory_and_credential_input_is_blocked_without_echo(self):
        request = self.request(matter="unused", private_memory="do not retain this private memory")
        result = load_helper().normalize_request(request)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertNotIn("do not retain", json.dumps(result).lower())
        self.assert_valid_output(result)

    def test_malformed_nested_input_is_blocked_without_echo(self):
        request = self.request(capability_requests=[{"capability_ref": "bad", "purpose": "invalid"}])
        result = load_helper().normalize_request(request)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["capability_requests"], [])
        self.assert_valid_output(result)

    def test_duplicate_evidence_and_identifiers_fail_closed(self):
        request = self.request(source_evidence=self.evidence() + self.evidence())
        result = load_helper().normalize_request(request)
        self.assertEqual(result["status"], "BLOCKED")
        self.assert_valid_output(result)
        duplicate = self.request(capability_requests=[self.request()["capability_requests"][0], self.request()["capability_requests"][0]])
        repeated = load_helper().normalize_request(duplicate)
        self.assertEqual(repeated["status"], "BLOCKED")
        self.assert_valid_output(repeated)

    def test_profile_hashes_and_cli_parse_failure_contract(self):
        self.assertEqual(verify_execution_profile_hashes(SKILL), [])
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "invalid.json"
            path.write_text("{", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SKILL / "scripts/helper_tool.py"), "--input", str(path)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "BLOCKED")
        self.assertEqual(output["effects"], {"messages_sent": [], "external_calls": [], "mutations": []})
        self.assert_valid_output(output)


if __name__ == "__main__":
    unittest.main()
