#!/usr/bin/env python3
"""Core policy unit tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))

from linkskills_core.certification import evaluate_certification_evidence  # noqa: E402
from linkskills_core.lifecycle import (  # noqa: E402
    TransitionError,
    assert_transition,
    can_transition,
)
from linkskills_core.retention import REDACTED, redact_payload, should_redact_key  # noqa: E402
from linkskills_core.selection import filter_compatible_usable_releases  # noqa: E402


class LifecycleTests(unittest.TestCase):
    def test_happy_path(self) -> None:
        self.assertTrue(can_transition("draft", "eval_pending"))
        self.assertTrue(can_transition("eval_pending", "usable"))
        self.assertTrue(can_transition("usable", "deprecated"))
        self.assertTrue(can_transition("deprecated", "retired"))

    def test_illegal_transition(self) -> None:
        self.assertFalse(can_transition("draft", "usable"))
        with self.assertRaises(TransitionError):
            assert_transition("retired", "usable")


class SelectionTests(unittest.TestCase):
    def test_filters_usable_compatible(self) -> None:
        releases = [
            {
                "skill_id": "a",
                "lifecycle_state": "usable",
                "compatible_runtime_profiles": ["cursor-macos"],
            },
            {
                "skill_id": "b",
                "lifecycle_state": "draft",
                "compatible_runtime_profiles": ["cursor-macos"],
            },
            {
                "skill_id": "c",
                "lifecycle_state": "usable",
                "compatible_runtime_profiles": ["codex-macos"],
            },
        ]
        selected = filter_compatible_usable_releases(releases, ["cursor-macos"])
        self.assertEqual([r["skill_id"] for r in selected], ["a"])


class RetentionTests(unittest.TestCase):
    def test_redacts_sensitive_keys(self) -> None:
        self.assertTrue(should_redact_key("api_key"))
        self.assertTrue(should_redact_key("hidden_reasoning"))
        self.assertTrue(should_redact_key("brain_transcript"))
        payload = {
            "run_id": "r1",
            "api_key": "sekrit",
            "nested": {"brain_transcript": "private", "ok": 1},
        }
        redacted = redact_payload(payload)
        self.assertEqual(redacted["run_id"], "r1")
        self.assertEqual(redacted["api_key"], REDACTED)
        self.assertEqual(redacted["nested"]["brain_transcript"], REDACTED)
        self.assertEqual(redacted["nested"]["ok"], 1)


class CertificationTests(unittest.TestCase):
    def test_refuses_prompt_only(self) -> None:
        decision = evaluate_certification_evidence(
            {
                "suite_id": "x",
                "rubric": ["correctness"],
                "pass_threshold": 0.8,
                "model_score": 0.9,
                "cases": [{"case_id": "c1", "score": 1.0}],
            }
        )
        self.assertFalse(decision.allowed)
        self.assertIn("executed case outputs", decision.reason)

    def test_refuses_suite_authored_observed_output_alone(self) -> None:
        decision = evaluate_certification_evidence(
            {
                "cases": [
                    {
                        "case_id": "c1",
                        "observed_output": "HELLO_CANARY",
                        "fixture_output": "HELLO_CANARY",
                    }
                ]
            }
        )
        self.assertFalse(decision.allowed)

    def test_accepts_executed_outputs(self) -> None:
        decision = evaluate_certification_evidence(
            {
                "cases": [
                    {
                        "case_id": "c1",
                        "executed_output": "observed result text",
                        "tool_traces": [{"tool_id": "gws", "status": "ok"}],
                    }
                ]
            }
        )
        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
