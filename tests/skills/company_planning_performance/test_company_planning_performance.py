from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "company-planning-performance"
REFS = SKILL / "references"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))
sys.path.insert(0, str(ROOT / "packages" / "core"))
from linkskills_contracts import validate_instance  # noqa: E402
from linkskills_core.hashing import verify_execution_profile_hashes  # noqa: E402


def load_helper():
    spec = importlib.util.spec_from_file_location("company_planning_helper", SKILL / "scripts" / "helper_tool.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request(**overrides):
    base = {
        "mode": "plan_review",
        "privacy_classification": "synthetic",
        "plan_ref": "plan:company-2026-q3",
        "horizon": "quarterly",
        "period": "2026-Q3",
        "source_evidence": [{"ref": "fixture:plan-001", "status": "confirmed"}],
        "objectives": [{"id": "objective:retention", "statement": "Improve evidence-backed retention.", "owner_ref": "owner:principal", "evidence_ref": "fixture:plan-001"}],
        "kpis": [{"id": "kpi:retention", "name": "Retention", "unit": "percent", "period": "2026-Q3", "target": 100, "forecast": 90, "actual": 84, "precision": "whole", "evidence_ref": "fixture:plan-001"}],
        "signals": [{"id": "signal:late-review", "status": "late", "note": "Review evidence arrived late.", "evidence_ref": "fixture:plan-001"}],
    }
    base.update(overrides)
    return base


class CompanyPlanningPerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = load_helper()
        cls.schemas = json.loads((REFS / "schemas.json").read_text(encoding="utf-8"))["definitions"]

    def assert_output_valid(self, output):
        schema = dict(self.schemas["output"])
        schema["definitions"] = self.schemas
        result = validate_instance(output, schema)
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])

    def test_required_artifacts_and_manifest_terms(self):
        required = [
            "SKILL.md", "advanced/advanced.md", "examples/success-pattern.md", "examples/error-recovery.md",
            "references/api-specs.md", "references/changelog.md", "references/eval-suite.json", "references/eval-suite.yaml",
            "references/execution-profile.json", "references/old-patterns.md", "references/schemas.json", "references/skill-pack.json",
            "scripts/README.md", "scripts/helper_tool.py",
        ]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        for marker in ("monthly", "rolling four-week", "quarterly", "annual", "three-year", "five-year", "objectives", "kpi", "forecast", "actual", "late", "blocked", "obsolete", "reprioritization", "evidence", "other — specify", "program", "task"):
            self.assertIn(marker, text, marker)

    def test_profile_and_eval_hashes_are_canonical(self):
        self.assertEqual(verify_execution_profile_hashes(SKILL), [])
        profile = json.loads((REFS / "execution-profile.json").read_text(encoding="utf-8"))
        suite_bytes = (REFS / "eval-suite.json").read_bytes()
        self.assertEqual(profile["eval_suite_hash"], "sha256:" + hashlib.sha256(suite_bytes).hexdigest())
        suite = json.loads(suite_bytes)
        self.assertEqual(suite["skill_id"], "company-planning-performance")
        self.assertEqual(len(suite["cases"]), 9)

    def test_valid_review_compares_forecast_actual_and_preserves_signals(self):
        result = self.helper.normalize_request(request())
        self.assertEqual(result["status"], "READY_FOR_OWNER")
        self.assertEqual(result["kpis"][0]["variance"], "-6")
        self.assertEqual(result["kpis"][0]["variance_status"], "COMPARABLE")
        self.assertEqual(result["signals"][0]["status"], "late")
        self.assertEqual(result["effects"], {"messages_sent": [], "external_calls": [], "mutations": []})
        self.assert_output_valid(result)

    def test_all_supported_horizons_are_explicit(self):
        for horizon in ("monthly", "rolling_4_week", "quarterly", "annual", "three_year", "five_year"):
            result = self.helper.normalize_request(request(horizon=horizon, period="2026-Q3"))
            self.assertIn(result["status"], {"READY_FOR_OWNER", "DRAFT"}, horizon)
            self.assertEqual(result["horizon"], horizon)
            self.assert_output_valid(result)

    def test_missing_actual_is_not_comparable_and_stays_draft(self):
        payload = request(kpis=[{**request()["kpis"][0], "actual": None}])
        result = self.helper.normalize_request(payload)
        self.assertEqual(result["status"], "DRAFT")
        self.assertEqual(result["kpis"][0]["variance_status"], "NOT_COMPARABLE")
        self.assertIsNone(result["kpis"][0]["variance"])
        self.assert_output_valid(result)

    def test_reprioritization_is_proposed_owner_review_only(self):
        result = self.helper.normalize_request(request(mode="reprioritization", reprioritization={"status": "proposed", "rationale": "Late evidence changes sequencing.", "objective_refs": ["objective:retention"], "evidence_ref": "fixture:plan-001"}))
        self.assertEqual(result["reprioritization"]["status"], "PROPOSED_FOR_OWNER")
        self.assertFalse(result["reprioritization"]["activated"])
        self.assertFalse(result["ownership"]["mutable_state_created"])
        self.assert_output_valid(result)

    def test_late_blocked_obsolete_signals_are_evidence_bound(self):
        signals = [{"id": f"signal:{state}", "status": state, "evidence_ref": "fixture:plan-001"} for state in ("late", "blocked", "obsolete", "on_track")]
        result = self.helper.normalize_request(request(signals=signals))
        self.assertEqual([row["status"] for row in result["signals"]], ["late", "blocked", "obsolete", "on_track"])
        self.assert_output_valid(result)

    def test_authority_privacy_precision_and_duplicate_boundaries_fail_closed(self):
        for action in ("approve", "activate", "schedule", "send", "create_task", "mutate_program"):
            result = self.helper.normalize_request(request(requested_action=action))
            self.assertEqual(result["status"], "BLOCKED", action)
            self.assert_output_valid(result)
        private = self.helper.normalize_request(request(matter="confidential company text"))
        self.assertEqual(private["status"], "BLOCKED")
        self.assertNotIn("confidential company text", json.dumps(private))
        precise = request(kpis=[{**request()["kpis"][0], "forecast": 90.1234, "precision": "two_decimal"}])
        self.assertEqual(self.helper.normalize_request(precise)["status"], "BLOCKED")
        duplicate = request(source_evidence=[{"ref": "fixture:plan-001", "status": "confirmed"}, {"ref": "fixture:plan-001", "status": "confirmed"}])
        self.assertEqual(self.helper.normalize_request(duplicate)["status"], "BLOCKED")

    def test_schema_rejects_effects_and_accepts_valid_result(self):
        result = self.helper.normalize_request(request())
        self.assert_output_valid(result)
        unsafe = deepcopy(result)
        unsafe["effects"]["mutations"] = ["task.create"]
        schema = dict(self.schemas["output"])
        schema["definitions"] = self.schemas
        self.assertFalse(validate_instance(unsafe, schema).ok)


if __name__ == "__main__":
    unittest.main()
