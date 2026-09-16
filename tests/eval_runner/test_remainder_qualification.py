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
        self.assertFalse(payload["usable_claimed"])
        self.assertFalse(payload["permission_to_act"])


if __name__ == "__main__":
    unittest.main()
