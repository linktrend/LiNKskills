from __future__ import annotations

import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "private-health-wellbeing"


def load_helper():
    spec = importlib.util.spec_from_file_location("private_health_helper", SKILL / "scripts" / "helper_tool.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PrivateHealthWellbeingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, str(ROOT / "packages" / "contracts"))
        from linkskills_contracts import validate_instance
        cls.validate_instance = staticmethod(validate_instance)
        cls.schemas = json.loads((SKILL / "references" / "schemas.json").read_text(encoding="utf-8"))["definitions"]

    def evidence(self):
        return [{"ref": "fixture:health-pkt12-001", "status": "confirmed"}]

    def request(self, mode="checkpoint", data=None):
        return {"mode": mode, "privacy_classification": "synthetic", "source_evidence": self.evidence(), "data": data or {}}

    def assert_valid_output(self, output):
        result = self.validate_instance(output, self.schemas["output"])
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])

    def test_required_artifacts_and_acceptance_surface(self):
        required = [
            "SKILL.md", "advanced/advanced.md", "examples/success-pattern.md", "examples/error-recovery.md",
            "references/api-specs.md", "references/changelog.md", "references/eval-suite.json",
            "references/eval-suite.yaml", "references/old-patterns.md", "references/schemas.json",
            "references/skill-pack.json", "scripts/README.md", "scripts/helper_tool.py",
        ]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        for marker in ("not_reported", "energy", "mood", "stress", "capacity", "hydration", "treatment", "dose", "protein", "spot-reduction", "sleep", "waist", "bowel", "uncertainty", "private consumer store"):
            self.assertIn(marker, skill)
        forbidden = "and guide you toward appropriate human or emergency support rather than waiting for the next checkpoint"
        self.assertNotIn(forbidden, " ".join(path.read_text(encoding="utf-8").lower() for path in SKILL.rglob("*.md")))

    def test_schema_is_strict_and_valid_checkpoint_is_evidence_complete(self):
        self.assertFalse(self.schemas["input"]["additionalProperties"])
        self.assertFalse(self.schemas["output"]["additionalProperties"])
        helper = load_helper()
        result = helper.normalize_request(self.request(data={"checkpoint_number": 1, "energy": 3, "mood": "not_reported", "stress": 2, "capacity_state": "steady"}))
        self.assertEqual(result["status"], "COMPLETED")
        self.assert_valid_output(result)
        self.assertEqual([item["field"] for item in result["observations"]], ["energy", "mood", "stress", "capacity_state"])
        self.assertEqual(result["effects"], {"external_calls": [], "mutations": [], "calendar_reminders": [], "messages_sent": [], "data_exports": []})

    def test_missing_private_data_and_redundant_questions_fail_closed(self):
        helper = load_helper()
        missing = helper.normalize_request({"mode": "initial_assessment", "privacy_classification": "synthetic", "source_evidence": []})
        self.assertEqual(missing["status"], "FAILED")
        self.assert_valid_output(missing)
        real = helper.normalize_request(self.request(data={"known_answers": ["sleep"], "requested_questions": ["sleep"], "sleep": "customer@example.com"}))
        self.assertEqual(real["status"], "FAILED")
        repeated = helper.normalize_request(self.request(data={"known_answers": ["sleep"], "requested_questions": ["sleep"]}))
        self.assertEqual(repeated["status"], "FAILED")
        self.assert_valid_output(repeated)

    def test_hydration_sleep_and_separate_measurements_are_deterministic(self):
        helper = load_helper()
        hydration = helper.normalize_request(self.request("hydration", {"bottle_ml": 1000, "remaining_ml": 250}))
        self.assertEqual(hydration["observations"][0]["value"], 750)
        self.assert_valid_output(hydration)
        sleep = helper.normalize_request(self.request("sleep", {"sleep_start": "2026-08-24T22:30:00+08:00", "sleep_end": "2026-08-25T06:30:00+08:00"}))
        self.assertEqual(sleep["observations"][0]["value"], 480)
        self.assert_valid_output(sleep)
        measure = helper.normalize_request(self.request("measurement", {"measurement_kind": "waist", "measurement_value": 80, "measurement_unit": "cm", "device": "synthetic-tape-1", "measurement_source": "fixture:waist-1"}))
        self.assertEqual(measure["observations"][0]["field"], "waist")
        self.assert_valid_output(measure)

    def test_treatment_image_exercise_and_reminder_boundaries(self):
        helper = load_helper()
        treatment = helper.normalize_request(self.request("treatment_appointment", {"treatment_record": {"kind": "dose_change_question", "owner_question": "Review supplied dose change"}}))
        self.assertEqual(treatment["status"], "PENDING_REVIEW")
        self.assert_valid_output(treatment)
        unsafe = helper.normalize_request(self.request("exercise", {"exercise_evidence": ["fixture:exercise-1"], "exercise_proposal": "Guaranteed spot reduction"}))
        self.assertEqual(unsafe["status"], "FAILED")
        photo = helper.normalize_request(self.request("meal_photo", {"photo_reference": "fixture:meal-photo-1"}))
        self.assertEqual(photo["status"], "FAILED")
        reminder = helper.normalize_request(self.request("calendar_reminder", {"reminder_key": "checkpoint:2026-08", "reminder_at": "2026-08-25T09:00:00+08:00"}))
        self.assertEqual(reminder["status"], "PENDING_REVIEW")
        self.assertEqual(reminder["effects"]["calendar_reminders"], [])
        self.assert_valid_output(reminder)

    def test_estimates_corrections_and_capacity_only_export(self):
        helper = load_helper()
        estimate = helper.normalize_request(self.request("nutrition", {"protein_estimate_g": 24, "estimate_basis": "synthetic label", "estimate_uncertainty": "brand serving not verified"}))
        self.assertEqual(estimate["status"], "COMPLETED")
        self.assert_valid_output(estimate)
        corrected = helper.normalize_request(self.request("meal_photo", {"photo_reference": "fixture:meal-photo-2", "image_uncertainty": "portion boundary unclear", "correction": "owner corrected portion class"}))
        self.assertEqual(corrected["status"], "COMPLETED")
        self.assert_valid_output(corrected)
        exported = helper.normalize_request(self.request("capacity_export", {"export_capacity_state": True, "capacity_state": "steady"}))
        self.assertEqual(exported["privacy"]["exportable_fields"], ["capacity_state"])
        self.assertEqual(exported["effects"]["data_exports"], [])
        self.assert_valid_output(exported)


if __name__ == "__main__":
    unittest.main()
