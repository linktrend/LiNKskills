"""Adversarial imported-content policy fixtures."""

import unittest

from linkskills_eval_runner.sandbox_v2 import (
    assess_candidate,
    plan_candidate,
    qualification_outcome,
)
from linkskills_eval_runner.models import EvalCase, EvalSuite
from linkskills_eval_runner.runner import run_suite


DIGEST = "sha256:" + "a" * 64
COMMIT = "b" * 40


def candidate(**overrides):
    value = {
        "source_identity": {
            "source_ref": "vendor:example@1.0.0",
            "source_commit": COMMIT,
            "source_path": "skills/example",
            "content_digest": DIGEST,
        },
        "release_identity": {
            "release_id": "example@1.0.0",
            "version": "1.0.0",
            "artifact_digest": DIGEST,
            "content_digest": DIGEST,
        },
        "declared_effects": ["stdout", "workspace_write"],
        "privacy_findings": [],
        "compatibility": "compatible",
        "licence": {"status": "approved"},
        "trust_boundary": "untrusted_external",
    }
    value.update(overrides)
    return value


class SandboxV2(unittest.TestCase):
    def test_attack_is_quarantined(self):
        with self.assertRaises(ValueError):
            plan_candidate({"declared_actions": ["network"], "paths": ["ok"]})

    def test_workspace_is_deterministic_and_failure_holds(self):
        a = plan_candidate({"declared_actions": [], "paths": ["a"]})
        b = plan_candidate({"declared_actions": [], "paths": ["a"]})
        self.assertEqual(a.workspace_id, b.workspace_id)
        self.assertEqual(qualification_outcome("escape"), "hold_quarantine")

    def test_clean_external_candidate_is_eligible(self):
        result = assess_candidate(candidate())
        self.assertTrue(result.admitted)
        self.assertEqual(result.outcome, "eligible_for_evaluation")
        self.assertTrue(result.candidate_digest.startswith("sha256:"))

    def test_prompt_injection_and_hidden_authority_are_quarantined(self):
        for finding in ("prompt_injection", "authority_escalation"):
            with self.subTest(finding=finding):
                result = assess_candidate(candidate(privacy_findings=[finding]))
                self.assertEqual(result.outcome, "hold_quarantine")
                self.assertIn("candidate:privacy_findings", result.reasons)

    def test_undeclared_effects_and_destructive_instructions_are_quarantined(self):
        missing = assess_candidate(candidate(declared_effects=[]))
        self.assertIn("candidate:declared_effects_missing", missing.reasons)
        destructive = assess_candidate(candidate(declared_effects=["destructive"]))
        self.assertIn("candidate:forbidden_effect:destructive", destructive.reasons)

    def test_licence_gap_and_digest_drift_are_quarantined(self):
        licence_gap = assess_candidate(candidate(licence={"status": "unknown"}))
        self.assertIn("candidate:licence_gap", licence_gap.reasons)
        drift = assess_candidate(candidate(observed_content_digest="sha256:" + "c" * 64))
        self.assertIn("candidate:digest_drift", drift.reasons)

    def test_private_data_and_production_mutation_are_quarantined(self):
        private = assess_candidate(candidate(privacy_findings=["private_data_leak"]))
        self.assertIn("candidate:privacy_findings", private.reasons)
        production = assess_candidate(candidate(active_production_mutation=True))
        self.assertIn("candidate:production_mutation_forbidden", production.reasons)

    def test_runner_quarantines_incomplete_external_metadata_before_execution(self):
        suite = EvalSuite(
            skill_id="external",
            suite_id="external-suite",
            suite_version="1.0.0",
            cases=[
                EvalCase(
                    id="malicious",
                    has_execute=True,
                    raw={
                        "execute": {"kind": "command", "argv": ["not-run"]},
                        "privacy_findings": ["prompt_injection"],
                    },
                    privacy_findings=["prompt_injection"],
                )
            ],
            raw={"privacy_findings": ["prompt_injection"]},
        )
        result = run_suite(suite)
        self.assertEqual(result.case_results[0].status.value, "quarantined")
        self.assertEqual(result.qualification_outcome, "hold_quarantine")


if __name__ == "__main__":
    unittest.main()
