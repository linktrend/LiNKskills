"""Remainder catalog qualification: 54 executable, never usable from source."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "packages" / "eval_runner"))
sys.path.insert(0, str(REPO / "packages" / "core"))

from linkskills_eval_runner.ed03 import INITIAL_RELEASE_PROFILES, REQUIRED_FAMILIES, case_records, classify_case_families
from linkskills_eval_runner.remainder import qualify_remainder_release_profiles, remainder_skill_ids


INITIAL = {item["skillId"] for item in INITIAL_RELEASE_PROFILES}


class RemainderQualificationTests(unittest.TestCase):
    def test_catalog_split(self) -> None:
        remaining = remainder_skill_ids(REPO)
        self.assertEqual(len(remaining), 54)
        self.assertTrue(INITIAL.isdisjoint(remaining))
        self.assertEqual(len(list((REPO / "skills").glob("*/SKILL.md"))), 59)

    def test_every_remainder_suite_is_executable_and_complete(self) -> None:
        for skill_id in remainder_skill_ids(REPO):
            records = case_records(REPO / "skills" / skill_id)
            self.assertTrue(records, skill_id)
            self.assertTrue(all(row.get("hasExecute") for row in records), skill_id)
            families = classify_case_families(records)
            self.assertEqual([name for name in REQUIRED_FAMILIES if not families[name]], [], skill_id)

    def test_matrix_never_claims_usable(self) -> None:
        matrix = qualify_remainder_release_profiles(REPO)
        self.assertTrue(matrix["ok"])
        self.assertFalse(matrix["usableClaimed"])
        self.assertFalse(matrix["authorizesUsable"])
        self.assertEqual(matrix["usable"], [])
        self.assertEqual(matrix["remainderCount"], 54)
        self.assertEqual(matrix["liveQualificationBoundary"], "server01_hosted_sealed_evaluator")

    def test_unknown_eval_case_fails_closed(self) -> None:
        skill = next(
            path
            for path in (REPO / "skills").glob("*/scripts/eval_driver.py")
        )
        proc = subprocess.run(
            [sys.executable, str(skill), "--case", "not-a-real-case"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "error")
        self.assertFalse(payload["permission_to_act"])
        self.assertFalse(payload["selectable"])

    def test_family_driver_emits_contract_status(self) -> None:
        driver = REPO / "skills" / "skill-architect" / "scripts" / "eval_driver.py"
        proc = subprocess.run(
            [sys.executable, str(driver), "--case", "remainder-guardrail-refuse-ungoverned-action"],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "REFUSED")
        self.assertFalse(payload["permission_to_act"])
        self.assertFalse(payload.get("production_claim"))
        self.assertNotIn("usable", json.dumps(payload))
        self.assertTrue(payload["ungoverned"])

    def test_golden_criteria_containing_block_is_not_automatically_blocked(self) -> None:
        from linkskills_eval_runner.remainder_driver import classify_contract_status

        self.assertEqual(
            classify_contract_status(
                "scaffold-new-stateless-simple-profile-skill",
                "golden",
            ),
            "PASS",
        )

    def test_legitimate_blocked_golden_case_passes_assertions(self) -> None:
        from linkskills_eval_runner.assertions import (
            assertions_passed,
            parse_assertion_spec,
            run_assertions,
        )
        from linkskills_eval_runner.remainder_driver import canonical_assertions

        case_id = "staged-diff-contains-secret-blocks-push"
        spec = parse_assertion_spec(canonical_assertions(case_id, "BLOCKED"))
        output = json.dumps(
            {
                "case_id": case_id,
                "status": "BLOCKED",
                "invalid": True,
                "permission_to_act": False,
                "certification_state": "draft",
            },
            indent=2,
            sort_keys=True,
        )
        results = run_assertions(output, spec, observed_exit_code=0)
        self.assertTrue(assertions_passed(results), results)

    def test_fixture_echo_bypass_fails_must_not_contain(self) -> None:
        from linkskills_eval_runner.assertions import (
            assertions_passed,
            parse_assertion_spec,
            run_assertions,
        )

        planted = json.dumps(
            {
                "status": "REFUSED",
                "case_id": "remainder-guardrail-refuse-ungoverned-action",
                "expected_criteria": ["Refuses the ungoverned shortcut"],
                "usable": True,
                "usable_claimed": True,
            },
            indent=2,
            sort_keys=True,
        )
        spec = parse_assertion_spec(
            {
                "must_contain": ["REFUSED", "remainder-guardrail-refuse-ungoverned-action"],
                "must_not_contain": ["usable"],
                "exit_code": 0,
            }
        )
        results = run_assertions(planted, spec, observed_exit_code=0)
        self.assertFalse(assertions_passed(results))
        self.assertTrue(any("must_not_contain" in row.name and not row.passed for row in results))

    def test_driver_does_not_echo_planted_expected_fields(self) -> None:
        driver = REPO / "skills" / "skill-architect" / "scripts" / "eval_driver.py"
        proc = subprocess.run(
            [sys.executable, str(driver), "--case", "scaffold-new-stateless-simple-profile-skill"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(REPO / "skills" / "skill-architect"),
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertNotIn("expected_criteria", payload)
        self.assertNotIn("contract_tokens", payload)
        self.assertNotIn("summary", payload)

    def test_remainder_eval_inputs_are_in_packaging_hash(self) -> None:
        from linkskills_core.hashing import build_skill_bundle_manifest

        skill = REPO / "skills" / "skill-architect"
        bundle = build_skill_bundle_manifest(skill)
        paths = {entry["path"] for entry in bundle["entry_hashes"]}
        self.assertIn("references/remainder-eval-cases.json", paths)
        self.assertIn("scripts/eval_driver.py", paths)


if __name__ == "__main__":
    unittest.main()
