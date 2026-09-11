"""Focused qualification of the five initial release/profile combinations."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.gitops.qualify_initial_release_profiles import (
    EVAL_PENDING,
    INITIAL_RELEASE_PROFILES,
    QUARANTINED,
    REQUIRED_FAMILIES,
    USABLE,
    classify_combination,
    classify_case_families,
    combination_id,
    delivery_secret_scan_preserved,
    qualify_initial_release_profiles,
    qualify_skill,
)

ROOT = Path(__file__).resolve().parents[2]


class InitialReleaseProfileQualificationTests(unittest.TestCase):
    def test_frozen_matrix_has_exactly_five_readme_combinations(self) -> None:
        self.assertEqual(len(INITIAL_RELEASE_PROFILES), 5)
        ids = [
            combination_id(row["skillId"], row["version"], row["runtimeProfile"])
            for row in INITIAL_RELEASE_PROFILES
        ]
        self.assertEqual(
            ids,
            [
                "git-safeguard@1.1.0/cursor-macos",
                "persistent-qa@1.0.0/cursor-macos",
                "repository-manager@1.0.0/cursor-macos",
                "skill-template@1.2.0/cursor-macos",
                "tool-architect@1.0.0/cursor-macos",
            ],
        )

    def test_source_matrix_classifies_each_combination_independently(self) -> None:
        matrix = qualify_initial_release_profiles(ROOT)
        self.assertTrue(matrix["complete"])
        self.assertEqual(len(matrix["combinations"]), 5)
        by_id = {row["id"]: row for row in matrix["combinations"]}
        self.assertEqual(set(by_id), set(matrix["evalPending"] + matrix["usable"] + matrix["quarantined"]))
        for declared in INITIAL_RELEASE_PROFILES:
            combo = combination_id(
                declared["skillId"], declared["version"], declared["runtimeProfile"]
            )
            row = by_id[combo]
            self.assertEqual(row["skillId"], declared["skillId"])
            self.assertEqual(row["runtimeProfile"], "cursor-macos")
            self.assertIn(row["lifecycle"], {EVAL_PENDING, USABLE, QUARANTINED})
            self.assertNotEqual(
                row["lifecycle"],
                USABLE,
                f"{combo} must not be usable without executed-case evidence",
            )

    def test_prompt_only_and_fake_evidence_cannot_become_usable(self) -> None:
        families = {name: ["case-a"] for name in REQUIRED_FAMILIES}
        fake = classify_combination(
            skill_id="git-safeguard",
            version="1.1.0",
            runtime_profile="cursor-macos",
            source_version="1.1.0",
            compatible_profiles=["cursor-macos"],
            families=families,
            executable_case_ids=["case-a"],
            evidence_kind="fake",
            certified=True,
        )
        prompt_only = classify_combination(
            skill_id="persistent-qa",
            version="1.0.0",
            runtime_profile="cursor-macos",
            source_version="1.0.0",
            compatible_profiles=["cursor-macos"],
            families=families,
            executable_case_ids=[],
            evidence_kind="prompt_only",
            certified=True,
        )
        self.assertEqual(fake["lifecycle"], QUARANTINED)
        self.assertEqual(prompt_only["lifecycle"], QUARANTINED)
        self.assertNotEqual(fake["lifecycle"], USABLE)
        self.assertNotEqual(prompt_only["lifecycle"], USABLE)

    def test_certified_without_execute_blocks_is_quarantined(self) -> None:
        row = classify_combination(
            skill_id="tool-architect",
            version="1.0.0",
            runtime_profile="cursor-macos",
            source_version="1.0.0",
            compatible_profiles=["cursor-macos"],
            families={name: ["golden"] for name in REQUIRED_FAMILIES},
            executable_case_ids=[],
            evidence_kind="independent",
            certified=True,
        )
        self.assertEqual(row["lifecycle"], QUARANTINED)
        self.assertEqual(row["reason"], "certified_without_executed_cases")

    def test_one_combination_failure_does_not_rewrite_siblings(self) -> None:
        healthy = classify_combination(
            skill_id="skill-template",
            version="1.2.0",
            runtime_profile="cursor-macos",
            source_version="1.2.0",
            compatible_profiles=["cursor-macos"],
            families={name: ["ok"] for name in REQUIRED_FAMILIES},
            executable_case_ids=["exec-1"],
            evidence_kind="executor",
            certified=True,
        )
        broken = classify_combination(
            skill_id="persistent-qa",
            version="1.0.0",
            runtime_profile="cursor-macos",
            source_version=None,
            compatible_profiles=[],
            families={name: [] for name in REQUIRED_FAMILIES},
            executable_case_ids=[],
        )
        self.assertEqual(healthy["lifecycle"], USABLE)
        self.assertEqual(broken["lifecycle"], EVAL_PENDING)
        self.assertEqual(healthy["skillId"], "skill-template")
        self.assertEqual(broken["skillId"], "persistent-qa")

    def test_missing_representative_families_are_diagnosed(self) -> None:
        families = classify_case_families(
            [
                {
                    "id": "clean-tree-full-checklist-allows-push",
                    "caseType": "golden",
                    "text": "clean tree allows push",
                },
                {
                    "id": "guardrail-refuse-push-without-checklist",
                    "caseType": "negative",
                    "text": "guardrail refuse",
                },
            ]
        )
        self.assertIn("clean-tree-full-checklist-allows-push", families["success"])
        self.assertIn("guardrail-refuse-push-without-checklist", families["guardrail"])
        row = qualify_skill(ROOT, INITIAL_RELEASE_PROFILES[0])
        self.assertEqual(row["skillId"], "git-safeguard")
        self.assertIn("privacy", row["families"])
        self.assertTrue(row["families"]["privacy"])
        self.assertIn("recovery", row["missingFamilies"])

    def test_persistent_qa_yaml_suite_is_classified_without_json(self) -> None:
        row = qualify_skill(ROOT, INITIAL_RELEASE_PROFILES[1])
        self.assertEqual(row["id"], "persistent-qa@1.0.0/cursor-macos")
        self.assertEqual(row["lifecycle"], EVAL_PENDING)
        self.assertTrue(row["families"]["guardrail"])
        self.assertTrue(row["families"]["recovery"])
        self.assertFalse(row["executableCases"])

    def test_fast_and_full_delivery_profiles_preserve_secret_scan(self) -> None:
        self.assertTrue(delivery_secret_scan_preserved(ROOT))
        payload = json.loads(
            (ROOT / ".ide-development" / "config" / "delivery.json").read_text(encoding="utf-8")
        )
        compile_argv = payload["profiles"]["fast"]["commands"][0]
        self.assertIn("scripts/gitops/qualify_initial_release_profiles.py", compile_argv)
        self.assertEqual(
            payload["profiles"]["fast"]["commands"][1],
            ["python3", "scripts/gitops/secret_scan.py"],
        )
        self.assertEqual(
            payload["profiles"]["full"]["commands"][1],
            ["python3", "scripts/gitops/secret_scan.py"],
        )


if __name__ == "__main__":
    unittest.main()
