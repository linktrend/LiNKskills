"""State-machine, projection, privacy, schema, and profile regressions for PKT-10."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "personal-compliance"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))
from linkskills_contracts import validate_instance  # noqa: E402


def load_helper():
    """Load the offline helper from the skill root."""

    spec = importlib.util.spec_from_file_location("personal_compliance_helper", SKILL / "scripts" / "helper_tool.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("helper spec unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPER = load_helper()
SCHEMA_DOCUMENT = json.loads((SKILL / "references" / "schemas.json").read_text(encoding="utf-8"))
SCHEMAS = SCHEMA_DOCUMENT["definitions"]
INPUT_SCHEMA = {**SCHEMA_DOCUMENT, "$ref": "#/definitions/input"}
EVIDENCE = [{"ref": "fixture:pc-demo-001", "status": "confirmed", "provenance": "synthetic-fixture", "licence": "internal"}]


def request(mode: str = "combined", **overrides):
    """Create a valid synthetic baseline request."""

    value = {
        "request_id": "pc-demo-001",
        "mode": mode,
        "privacy_classification": "synthetic",
        "source_evidence": EVIDENCE,
        "configuration": {
            "valid_window": {"start": "18:00", "end": "22:00"},
            "upper_target": 98,
            "alert_threshold": 35,
            "next_charge_hours": 2,
            "minimum_rate_observations": 2,
            "checkpoint": "routine",
        },
    }
    value.update(overrides)
    return value


def battery_observations():
    """Return synthetic charge/discharge observations with two rates each."""

    return [
        {"timestamp_hours": 0, "percentage": 30, "plugged": False, "charger_key": "fixture:charger-a", "location_key": "fixture:location-a"},
        {"timestamp_hours": 1, "percentage": 25, "plugged": False, "charger_key": "fixture:charger-a", "location_key": "fixture:location-a"},
        {"timestamp_hours": 2, "percentage": 25, "plugged": True, "charger_key": "fixture:charger-a", "location_key": "fixture:location-a"},
        {"timestamp_hours": 3, "percentage": 45, "plugged": True, "charger_key": "fixture:charger-a", "location_key": "fixture:location-a"},
        {"timestamp_hours": 4, "percentage": 45, "plugged": False, "charger_key": "fixture:charger-a", "location_key": "fixture:location-a"},
        {"timestamp_hours": 5, "percentage": 40, "plugged": False, "charger_key": "fixture:charger-a", "location_key": "fixture:location-a"},
        {"timestamp_hours": 6, "percentage": 40, "plugged": True, "charger_key": "fixture:charger-a", "location_key": "fixture:location-a"},
        {"timestamp_hours": 7, "percentage": 60, "plugged": True, "charger_key": "fixture:charger-a", "location_key": "fixture:location-a"},
    ]


class PersonalComplianceTests(unittest.TestCase):
    """Verify the complete PKT-10 acceptance surface."""

    def assert_output(self, output):
        """Require a complete output contract and no effects."""

        checked = validate_instance(output, SCHEMAS["output"])
        self.assertTrue(checked.ok, checked.errors)
        self.assertEqual(output["effects"], {"external_calls": [], "messages_sent": [], "mutations": [], "private_state_writes": False})
        self.assertEqual(output["rollback"], HELPER.ROLLBACK_TARGET)

    def test_required_artifacts_and_acceptance_terms(self):
        required = [
            "SKILL.md", "advanced/advanced.md", "examples/success-pattern.md", "examples/error-recovery.md",
            "references/api-specs.md", "references/changelog.md", "references/old-patterns.md",
            "references/eval-suite.json", "references/eval-suite.yaml", "references/schemas.json",
            "references/skill-pack.json", "references/execution-profile.json", "scripts/helper_tool.py",
        ]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("selfie", "EARLY", "COMPLETED", "REPORTED_LATE", "MISSED", "battery", "saturation", "35%", "silent", "final checkpoint", "image", "uncertainty", "correction", "privacy", "PENDING_APPROVAL", "native CLI", "direct api", "specialist"):
            self.assertIn(phrase, body, phrase)
        for forbidden in ("18:00", "22:00", "98%", "fixture:image-real", "customer@example.com", "BEGIN PRIVATE KEY"):
            self.assertNotIn(forbidden, body)

    def test_input_schema_is_strict_and_valid_baseline_accepts(self):
        self.assertTrue(validate_instance(request(), INPUT_SCHEMA).ok)
        invalid = request()
        invalid["mode"] = "unlisted"
        self.assertFalse(validate_instance(invalid, INPUT_SCHEMA).ok)
        invalid_action = request()
        invalid_action["requested_actions"] = ["publish"]
        self.assertFalse(validate_instance(invalid_action, INPUT_SCHEMA).ok)

    def test_selfie_states_and_late_is_distinct(self):
        for capture, expected in (("17:30", "EARLY"), ("20:00", "COMPLETED"), ("22:30", "REPORTED_LATE")):
            with self.subTest(capture=capture):
                result = HELPER.normalize_request(request("selfie_compliance", selfie={"capture_time": capture, "window_closed": True}))
                self.assertEqual(result["state_transition"]["state"], expected)
                self.assert_output(result)
        missed = HELPER.normalize_request(request("selfie_compliance", selfie={"window_closed": True}))
        self.assertEqual(missed["state_transition"]["state"], "MISSED")
        self.assertEqual(missed["status"], "PENDING_APPROVAL")
        self.assert_output(missed)

    def test_reminders_are_conditional_and_deduplicated(self):
        proposed = HELPER.normalize_request(request("selfie_compliance", selfie={"window_closed": False, "reminder_kind": "first"}))
        self.assertEqual(proposed["reminders"]["proposed"], ["conditional:first"])
        duplicate = HELPER.normalize_request(request("selfie_compliance", selfie={"window_closed": False, "reminder_kind": "first", "existing_reminder_refs": ["fixture:reminder-first"]}))
        self.assertTrue(duplicate["reminders"]["suppressed"])
        self.assertEqual(duplicate["reminders"]["duplicate_of"], "fixture:reminder-first")
        self.assert_output(proposed)
        self.assert_output(duplicate)

    def test_battery_learns_rates_projects_threshold_and_preserves_maintenance(self):
        config = {**request("battery_tracking")["configuration"], "next_charge_hours": 6}
        result = HELPER.normalize_request(request("battery_tracking", configuration=config, battery={"observations": battery_observations(), "maintenance_active": True}))
        self.assertTrue(result["battery_projection"]["available"])
        self.assertTrue(result["battery_projection"]["alert"])
        self.assertFalse(result["battery_projection"]["maintenance_cancelled"])
        self.assertIn("learned-rates", result["battery_projection"]["rate_labels"])
        self.assertIn("saturation-aware-charge-estimate", result["battery_projection"]["rate_labels"])
        self.assert_output(result)

    def test_silent_no_alert_has_no_reminder(self):
        config = {**request("battery_tracking")["configuration"], "next_charge_hours": 1}
        result = HELPER.normalize_request(request("battery_tracking", configuration=config, battery={"observations": battery_observations()}))
        self.assertFalse(result["battery_projection"]["alert"])
        self.assertIn("silent-no-alert", result["battery_projection"]["rate_labels"])
        self.assertEqual(result["reminders"]["proposed"], [])
        self.assert_output(result)

    def test_measurement_bundle_and_final_checkpoint_do_not_request_next(self):
        config = {**request()["configuration"], "checkpoint": "final"}
        result = HELPER.normalize_request(request("selfie_compliance", configuration=config, measurements=["sleep", "battery", "mood"]))
        self.assertEqual(result["measurements"]["bundled"], ["battery", "mood", "sleep"])
        self.assertTrue(result["measurements"]["final_checkpoint"])
        self.assertFalse(result["measurements"]["next_checkpoint_requested"])
        self.assert_output(result)

    def test_image_ambiguity_and_correction_history_preserve_prior(self):
        result = HELPER.normalize_request(request("selfie_compliance", image={"image_ref": "fixture:image-demo", "extractions": [{"field": "battery_percent", "value": "62", "confidence": "low", "material": True}, {"field": "capture_marker", "value": "visible", "confidence": "high", "material": True}], "corrections": [{"field": "battery_percent", "prior_value": "62", "proposed_value": "63", "reason": "synthetic review"}]}))
        self.assertEqual(result["image_review"]["confirmations_needed"], ["battery_percent"])
        self.assertEqual(result["image_review"]["confirmed"], ["capture_marker=visible"])
        self.assertIn("prior=62", result["image_review"]["correction_history"][0])
        self.assertIn("proposed=63", result["image_review"]["correction_history"][0])
        self.assert_output(result)

    def test_privacy_missing_evidence_and_authority_fail_closed_without_echo(self):
        private = request()
        private["privacy_classification"] = "restricted"
        private["secret"] = "do-not-echo"
        rejected = HELPER.normalize_request(private)
        self.assertEqual(rejected["status"], "FAILED")
        self.assertNotIn("do-not-echo", json.dumps(rejected))
        missing = request()
        missing["source_evidence"] = [{"ref": "fixture:pc-demo-001", "status": "confirmed", "licence": "internal"}]
        self.assertEqual(HELPER.normalize_request(missing)["status"], "FAILED")
        action = request()
        action["requested_actions"] = ["send"]
        self.assertEqual(HELPER.normalize_request(action)["status"], "PENDING_APPROVAL")
        self.assert_output(rejected)
        self.assert_output(HELPER.normalize_request(missing))
        self.assert_output(HELPER.normalize_request(action))

    def test_unknown_mode_and_not_reported_evidence_escalate(self):
        unknown = HELPER.normalize_request(request("other"))
        self.assertEqual(unknown["disposition"], "clarification")
        not_reported = request()
        not_reported["source_evidence"] = [{**EVIDENCE[0], "status": "not_reported"}]
        pending = HELPER.normalize_request(not_reported)
        self.assertEqual(pending["disposition"], "needs-evidence")
        self.assert_output(unknown)
        self.assert_output(pending)

    def test_helper_is_deterministic_and_offline(self):
        value = request("battery_tracking", battery={"observations": battery_observations()})
        self.assertEqual(HELPER.normalize_request(value), HELPER.normalize_request(value))
        source = (SKILL / "scripts/helper_tool.py").read_text(encoding="utf-8")
        for forbidden in ("requests", "urllib", "socket", "subprocess", "device.read", "calendar.create", "reminder.send"):
            self.assertNotIn(forbidden, source)
        self.assertRegex(HELPER.normalize_request(value)["idempotency_key"], r"^pc-[a-f0-9]{16}$")

    def test_profile_and_eval_hash_fields_are_bound(self):
        profile = json.loads((SKILL / "references" / "execution-profile.json").read_text(encoding="utf-8"))
        suite = json.loads((SKILL / "references" / "eval-suite.json").read_bytes())
        self.assertEqual(profile["eval_suite_id"], suite["suite_id"])
        self.assertEqual(profile["eval_suite_hash"], "sha256:" + hashlib.sha256((SKILL / "references" / "eval-suite.json").read_bytes()).hexdigest())
        self.assertRegex(profile["skill_bundle_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(profile["profile_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertGreaterEqual(len(suite["cases"]), 10)


if __name__ == "__main__":
    unittest.main()
