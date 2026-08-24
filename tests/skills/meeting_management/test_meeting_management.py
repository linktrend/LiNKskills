"""Agenda, transcript privacy, routing, candidate, and follow-up tests."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "meeting-management"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))
sys.path.insert(0, str(ROOT / "packages" / "core"))
from linkskills_contracts import validate_instance  # noqa: E402
from linkskills_core.hashing import verify_execution_profile_hashes  # noqa: E402


def load_helper():
    """Load the offline helper from the skill package."""

    spec = importlib.util.spec_from_file_location("meeting_management_helper", SKILL / "scripts/helper_tool.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPER = load_helper()
DOCUMENT = json.loads((SKILL / "references/schemas.json").read_text(encoding="utf-8"))
EVIDENCE = [{"ref": "fixture:meeting-source-001", "status": "confirmed", "provenance": "synthetic-fixture", "licence": "internal"}]


def request(**overrides):
    """Build a valid synthetic meeting request."""

    value = {
        "request_id": "mm-demo-001",
        "mode": "full",
        "privacy_classification": "synthetic",
        "source_evidence": EVIDENCE,
        "requested_actions": ["prepare", "summarize", "extract", "route"],
        "meeting": {
            "meeting_ref": "fixture:meeting-demo-001",
            "purpose": "Choose a bounded launch decision",
            "owner": "fixture:participant-principal",
            "desired_decision": "Select the evidence-backed option",
            "participants": ["fixture:participant-principal", "fixture:participant-lisa"],
            "agenda_items": ["Review evidence", "Choose option"],
            "transcript_ref": "fixture:transcript-demo-001",
            "transcript_hash": "sha256:" + "a" * 64,
            "redacted_notes": "Evidence was reviewed; one owner will prepare the next bounded result.",
            "decisions": [{"decision_ref": "fixture:decision-demo-001", "statement": "Keep the work bounded", "owner": "fixture:participant-principal", "evidence_ref": "fixture:meeting-source-001", "confidence": "high"}],
            "follow_ups": [{"follow_up_ref": "fixture:followup-demo-001", "title": "Prepare evidence brief", "owner": "fixture:participant-lisa", "deadline": "fixture:next-review", "dependency": "fixture:source-review", "destination_mappings": {"google_tasks": "fixture:google-task-1", "agent_store": "fixture:agent-task-2"}, "status": "Assigned"}],
            "candidate": {"candidate_ref": "fixture:candidate-demo-001", "last_reviewed": "fixture:last-review", "attendance_signal": "sufficient", "decision_value": "high", "duplicate_risk": False, "next_review_date": "fixture:next-review"},
        },
    }
    value.update(overrides)
    return value


class MeetingManagementTests(unittest.TestCase):
    """Verify the complete PKT-18 acceptance surface."""

    def assert_output(self, output):
        """Require strict output, privacy flags, and empty effects."""

        checked = validate_instance(output, {**DOCUMENT, "$ref": "#/definitions/output"})
        self.assertTrue(checked.ok, checked.errors)
        self.assertEqual(output["effects"], {"external_calls": [], "messages_sent": [], "mutations": [], "private_state_writes": False})
        self.assertFalse(output["privacy"]["raw_transcript_retained"])
        self.assertEqual(output["rollback"], HELPER.ROLLBACK_TARGET)

    def test_required_artifacts_and_boundaries(self):
        required = ["SKILL.md", "advanced/advanced.md", "examples/success-pattern.md", "examples/error-recovery.md", "references/api-specs.md", "references/changelog.md", "references/old-patterns.md", "references/eval-suite.json", "references/eval-suite.yaml", "references/schemas.json", "references/skill-pack.json", "references/execution-profile.json", "scripts/helper_tool.py"]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for marker in ("agenda", "private pre-brief", "redacted notes", "transcript", "decisions", "commitments", "tasks", "Google", "agent", "follow-up", "Verified", "maintained", "specialist", "generalist", "PENDING_APPROVAL", "cli wrapper", "MCP"):
            self.assertIn(marker, text, marker)
        for forbidden in ("customer@example.com", "BEGIN PRIVATE KEY", "send_minutes: true", "calendar.create"):
            self.assertNotIn(forbidden, text)

    def test_agenda_prebrief_notes_and_reference_only_routing(self):
        result = HELPER.normalize_request(request())
        self.assert_output(result)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["agenda"]["objective"], "Choose a bounded launch decision")
        self.assertTrue(result["prebrief"]["private"])
        self.assertFalse(result["prebrief"]["shared_routing_allowed"])
        self.assertIn("Evidence was reviewed", result["notes"]["summary"])
        self.assertEqual(result["follow_ups"][0]["destination_mappings"]["google_tasks"], "fixture:google-task-1")

    def test_decision_and_candidate_maintenance(self):
        result = HELPER.normalize_request(request(mode="candidate_review"))
        self.assert_output(result)
        self.assertEqual(result["decisions"][0]["decision_ref"], "fixture:decision-demo-001")
        self.assertIn("Other — specify", result["decisions"][0]["alternatives"])
        self.assertTrue(result["candidate_review"]["included"])
        self.assertEqual(result["candidate_review"]["disposition"], "maintain")
        self.assertFalse(result["candidate_review"]["schedule_mutated"])

    def test_followup_verification_requires_receipt(self):
        follow = {**request()["meeting"]["follow_ups"][0], "status": "Verified"}
        pending = HELPER.normalize_request(request(meeting={**request()["meeting"], "follow_ups": [follow]}))
        self.assertEqual(pending["status"], "PENDING_APPROVAL")
        self.assertEqual(pending["follow_ups"][0]["status"], "Awaiting evidence")
        verified = {**follow, "verification_ref": "fixture:verification-demo-001"}
        complete = HELPER.normalize_request(request(meeting={**request()["meeting"], "follow_ups": [verified]}))
        self.assertEqual(complete["status"], "COMPLETED")
        self.assertEqual(complete["follow_ups"][0]["status"], "Verified")
        self.assert_output(complete)

    def test_authority_actions_fail_closed(self):
        for action in ("send", "create", "update", "retire", "reschedule"):
            result = HELPER.normalize_request(request(requested_actions=[action]))
            self.assertEqual(result["status"], "PENDING_APPROVAL")
            self.assertEqual(result["candidate_review"]["schedule_mutated"], False)
            self.assert_output(result)

    def test_raw_transcript_and_restricted_input_fail_without_echo(self):
        raw = request(transcript_text="private participant statement that must not echo")
        rejected = HELPER.normalize_request(raw)
        self.assertEqual(rejected["status"], "FAILED")
        self.assertNotIn("private participant statement", json.dumps(rejected))
        restricted = HELPER.normalize_request(request(privacy_classification="restricted"))
        self.assertEqual(restricted["status"], "FAILED")
        self.assert_output(rejected)
        self.assert_output(restricted)

    def test_missing_or_unknown_evidence_is_pending(self):
        missing = HELPER.normalize_request(request(source_evidence=[]))
        self.assertEqual(missing["status"], "FAILED")
        unknown = HELPER.normalize_request(request(source_evidence=[{"ref": "fixture:meeting-source-001", "status": "unknown", "provenance": "synthetic", "licence": "internal"}]))
        self.assertEqual(unknown["status"], "PENDING_APPROVAL")
        self.assert_output(unknown)

    def test_determinism_and_profile_hashes(self):
        first = HELPER.normalize_request(request())
        self.assertEqual(first, HELPER.normalize_request(request()))
        self.assertRegex(first["idempotency_key"], r"^mm-[a-f0-9]{16}$")
        profile = json.loads((SKILL / "references/execution-profile.json").read_text(encoding="utf-8"))
        suite = json.loads((SKILL / "references/eval-suite.json").read_bytes())
        self.assertEqual(profile["eval_suite_id"], suite["suite_id"])
        self.assertEqual(profile["eval_suite_hash"], "sha256:" + hashlib.sha256((SKILL / "references/eval-suite.json").read_bytes()).hexdigest())
        self.assertEqual(verify_execution_profile_hashes(SKILL), [])
        self.assertGreaterEqual(len(suite["cases"]), 10)

    def test_malformed_cli_input_preserves_failure_contract(self):
        helper_path = SKILL / "scripts" / "helper_tool.py"
        completed = subprocess.run([sys.executable, str(helper_path)], input="[]", text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 1)
        self.assert_output(json.loads(completed.stdout))


if __name__ == "__main__":
    unittest.main()
