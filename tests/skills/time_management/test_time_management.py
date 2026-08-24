"""Contract, priority, capacity, evidence, and ownership tests for PKT-11."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "time-management"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))
sys.path.insert(0, str(ROOT / "packages" / "core"))
from linkskills_contracts import validate_instance  # noqa: E402
from linkskills_core.hashing import verify_execution_profile_hashes  # noqa: E402


def load_helper():
    """Load the offline helper without installing the skill."""

    spec = importlib.util.spec_from_file_location("time_management_helper", SKILL / "scripts" / "helper_tool.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPER = load_helper()
DOCUMENT = json.loads((SKILL / "references/schemas.json").read_text(encoding="utf-8"))
SCHEMAS = DOCUMENT["definitions"]
EVIDENCE = [{"ref": "fixture:tm-demo-001", "status": "confirmed", "provenance": "synthetic-fixture", "licence": "internal"}]
PERIODS = [
    {"period_id": "fixture:period-easy", "label": "Morning easy", "difficulty": "easy", "protected": True},
    {"period_id": "fixture:period-medium", "label": "Midday medium", "difficulty": "medium", "protected": True},
    {"period_id": "fixture:period-hard", "label": "Afternoon hard", "difficulty": "hard", "protected": True},
    {"period_id": "fixture:period-flex", "label": "Flexible", "difficulty": "flexible", "protected": True},
    {"period_id": "fixture:period-break", "label": "Break", "difficulty": "break", "protected": True},
]


def request(**overrides):
    """Build a valid synthetic planning request."""

    value = {
        "request_id": "tm-demo-001",
        "mode": "plan",
        "privacy_classification": "synthetic",
        "source_evidence": EVIDENCE,
        "tasks": [{"task_id": "T-000042", "title": "Prepare weekly outcome", "confirmation": "Confirmed", "owner": "Principal", "importance": "high", "difficulty": "medium", "estimated_periods": 1, "deadline": "fixture:tomorrow", "dependencies": [], "unlocks": ["fixture:follow-up"], "external_mappings": {"google_tasks": "fixture:google-42", "brain": "fixture:brain-7", "program": "fixture:program-3", "handoff": "fixture:handoff-1"}, "status": "Ready", "evidence_refs": ["fixture:tm-demo-001"]}],
        "capacity": {"state": "normal", "periods": PERIODS, "overdue_principal_work": False, "ready_current_week": True, "resolvable_blocker": False, "deadline_at_risk": False, "useful_action_before_next_workday": True},
        "requested_actions": ["prepare"],
        "review": {"result_known": False, "acknowledged": False},
    }
    value.update(overrides)
    return value


class TimeManagementTests(unittest.TestCase):
    """Verify the complete PKT-11 acceptance surface."""

    def assert_output(self, output):
        """Require strict output and an empty-effects envelope."""

        checked = validate_instance(output, {**DOCUMENT, "$ref": "#/definitions/output"})
        self.assertTrue(checked.ok, checked.errors)
        self.assertEqual(output["effects"], {"external_calls": [], "messages_sent": [], "mutations": [], "private_state_writes": False})
        self.assertEqual(output["rollback"], HELPER.ROLLBACK_TARGET)

    def test_required_artifacts_and_acceptance_terms(self):
        required = ["SKILL.md", "advanced/advanced.md", "examples/success-pattern.md", "examples/error-recovery.md", "references/api-specs.md", "references/changelog.md", "references/old-patterns.md", "references/eval-suite.json", "references/eval-suite.yaml", "references/schemas.json", "references/skill-pack.json", "references/execution-profile.json", "scripts/helper_tool.py"]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for marker in ("Confirmed", "Provisional", "T-", "SQLite", "Awaiting for other", "Verified complete", "Completed — Carlos reported", "protected", "flexible", "four-week", "Monday", "mobile-friendly", "morning", "evening", "monthly", "standing-rule", "PENDING_APPROVAL", "specialist", "read-only"):
            self.assertIn(marker, text, marker)
        for forbidden in ("18:00", "22:00", "customer@example.com", "BEGIN PRIVATE KEY"):
            self.assertNotIn(forbidden, text)

    def test_valid_schema_and_stable_mappings(self):
        self.assertTrue(validate_instance(request(), {**DOCUMENT, "$ref": "#/definitions/input"}).ok)
        first = HELPER.normalize_request(request())
        second = HELPER.normalize_request(request())
        self.assert_output(first)
        self.assertEqual(first, second)
        item = first["items"][0]
        self.assertEqual(item["task_id"], "T-000042")
        self.assertEqual(item["external_mappings"]["google_tasks"], "fixture:google-42")
        self.assertEqual(first["status"], "COMPLETED")

    def test_priority_deadline_and_unblocking_precede_optional(self):
        tasks = [
            {"title": "Optional polish", "confirmation": "Confirmed", "owner": "Principal", "importance": "low", "difficulty": "easy", "estimated_periods": 1, "status": "Ready"},
            {"title": "Unblock reviewer", "confirmation": "Confirmed", "owner": "Lisa", "importance": "normal", "difficulty": "hard", "estimated_periods": 1, "dependencies": ["fixture:review"], "status": "Ready"},
            {"title": "Immovable deadline", "confirmation": "Confirmed", "owner": "Principal", "importance": "normal", "difficulty": "medium", "estimated_periods": 1, "deadline": "fixture:today", "status": "Ready"},
        ]
        result = HELPER.normalize_request(request(tasks=tasks))
        self.assert_output(result)
        titles = [item["title"] for item in result["items"]]
        self.assertEqual(titles[:2], ["Immovable deadline", "Unblock reviewer"])

    def test_provisional_and_authority_are_fail_closed(self):
        provisional = request(tasks=[{**request()["tasks"][0], "confirmation": "Provisional"}])
        self.assertEqual(HELPER.normalize_request(provisional)["status"], "PENDING_APPROVAL")
        for action in ("schedule", "send", "commit", "activate"):
            result = HELPER.normalize_request(request(requested_actions=[action]))
            self.assertEqual(result["status"], "PENDING_APPROVAL")
            self.assert_output(result)

    def test_agent_completion_requires_evidence_principal_report_is_accepted(self):
        agent = {**request()["tasks"][0], "owner": "Lisa", "status": "Verified complete"}
        pending = HELPER.normalize_request(request(tasks=[agent]))
        self.assertEqual(pending["items"][0]["status"], "Awaiting agent evidence")
        self.assertEqual(pending["status"], "PENDING_APPROVAL")
        principal = {**agent, "owner": "Principal", "status": "Completed — Carlos reported"}
        complete = HELPER.normalize_request(request(tasks=[principal]))
        self.assertEqual(complete["items"][0]["status"], "Completed — Carlos reported")
        self.assert_output(complete)

    def test_capacity_flexible_period_and_reviews(self):
        capacity = {**request()["capacity"], "state": "reduced", "ready_current_week": False, "useful_action_before_next_workday": False}
        result = HELPER.normalize_request(request(capacity=capacity, review={"result_known": True, "acknowledged": False}))
        self.assertTrue(result["capacity_decision"]["time_off_question"])
        self.assertFalse(result["capacity_decision"]["health_cause_included"])
        self.assertEqual(result["flexible_period"]["decision"], "personal")
        self.assertFalse(result["reviews"]["acknowledgement_inferred"])
        self.assertFalse(result["reviews"]["end_check"]["requested"])
        self.assert_output(result)

    def test_standing_rule_is_proposed_never_activated(self):
        result = HELPER.normalize_request(request(mode="standing_rule", standing_rule={"trigger": "fixture:trigger", "automatic_action": "prepare review", "exceptions": ["fixture:exception"], "affected_agents_or_systems": ["consumer"], "permanence_or_review_date": "fixture:review-date"}))
        self.assertTrue(result["standing_rule"]["proposed"])
        self.assertFalse(result["standing_rule"]["activated"])
        self.assert_output(result)

    def test_privacy_and_missing_evidence_do_not_echo(self):
        private = request(secret="do-not-echo")
        rejected = HELPER.normalize_request(private)
        self.assertEqual(rejected["status"], "FAILED")
        self.assertNotIn("do-not-echo", json.dumps(rejected))
        missing = request(source_evidence=[{"ref": "fixture:tm-demo-001", "status": "unknown", "provenance": "synthetic-fixture", "licence": "internal"}])
        self.assertEqual(HELPER.normalize_request(missing)["status"], "PENDING_APPROVAL")

    def test_profile_and_eval_hashes_are_bound(self):
        profile = json.loads((SKILL / "references/execution-profile.json").read_text(encoding="utf-8"))
        suite = json.loads((SKILL / "references/eval-suite.json").read_bytes())
        self.assertEqual(profile["eval_suite_id"], suite["suite_id"])
        self.assertEqual(profile["eval_suite_hash"], "sha256:" + hashlib.sha256((SKILL / "references/eval-suite.json").read_bytes()).hexdigest())
        self.assertEqual(verify_execution_profile_hashes(SKILL), [])
        self.assertGreaterEqual(len(suite["cases"]), 12)


if __name__ == "__main__":
    unittest.main()
