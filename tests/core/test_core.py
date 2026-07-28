#!/usr/bin/env python3
"""Core policy unit tests."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault(
    "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
    "linkskills-local-eval-runner-issuer-key-not-for-production",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))

from linkskills_core.certification import (  # noqa: E402
    evaluate_certification_evidence,
    sealed_executor_receipt,
)
from linkskills_core.lifecycle import (  # noqa: E402
    TransitionError,
    assert_transition,
    can_transition,
)
from linkskills_core.retention import REDACTED, redact_payload, should_redact_key  # noqa: E402
from linkskills_core.selection import filter_compatible_usable_releases  # noqa: E402


def _seal_receipt(**overrides):
    """Build a sealed executor receipt matching core/eval seal contract."""
    import hmac
    import os

    base = {
        "receipt_id": "rcpt-1",
        "case_id": "c1",
        "skill_id": "demo",
        "suite_id": "suite-1",
        "suite_hash": "suitehash",
        "skill_release_hash": "skill-release:abc123",
        "execution_profile_hash": "profilehash",
        "environment": {"python_version": "3.11"},
        "toolchain": {"kind": "test"},
        "tool_calls": [],
        "exit_code": 0,
        "stdout_hash": "stdout",
        "stderr_hash": "stderr",
        "artifact_hashes": [],
        "started_at": "2026-07-28T00:00:00Z",
        "finished_at": "2026-07-28T00:00:01Z",
        "executor_version": "linkskills-eval-executor/0.3.0",
        "evidence_source": "executor",
        "provenance_kind": "eval_runner_hmac_v1",
        "issuer_id": "linkskills-eval-runner-test",
    }
    base.update(overrides)
    payload = {
        "artifact_hashes": list(base.get("artifact_hashes") or []),
        "case_id": base["case_id"],
        "environment": dict(base.get("environment") or {}),
        "evidence_source": base["evidence_source"],
        "execution_profile_hash": base["execution_profile_hash"],
        "executor_version": base["executor_version"],
        "exit_code": base.get("exit_code"),
        "finished_at": base["finished_at"],
        "issuer_id": base["issuer_id"],
        "provenance_kind": base["provenance_kind"],
        "receipt_id": base["receipt_id"],
        "skill_id": base["skill_id"],
        "skill_release_hash": base["skill_release_hash"],
        "started_at": base["started_at"],
        "stderr_hash": base["stderr_hash"],
        "stdout_hash": base["stdout_hash"],
        "suite_hash": base["suite_hash"],
        "suite_id": base["suite_id"],
        "tool_calls": list(base.get("tool_calls") or []),
        "toolchain": dict(base.get("toolchain") or {}),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()
    base["receipt_hash"] = digest
    key = os.environ.get(
        "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
        "linkskills-local-eval-runner-issuer-key-not-for-production",
    ).encode("utf-8")
    base["issuer_signature"] = hmac.new(key, digest.encode("utf-8"), hashlib.sha256).hexdigest()
    return base


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
        self.assertIn("receipt", decision.reason.lower())

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

    def test_refuses_bare_output_and_tool_traces(self) -> None:
        decision = evaluate_certification_evidence(
            {
                "cases": [
                    {
                        "case_id": "c1",
                        "executed_output": "observed result text",
                        "output": "bare string",
                        "tool_traces": [{"tool_id": "gws", "status": "ok"}],
                        "artifact_refs": ["a1"],
                    }
                ]
            }
        )
        self.assertFalse(decision.allowed)
        self.assertIn("receipt", decision.reason)

    def test_refuses_fabricated_receipt_hash(self) -> None:
        receipt = _seal_receipt()
        receipt["receipt_hash"] = "0" * 64
        self.assertFalse(sealed_executor_receipt(receipt))
        decision = evaluate_certification_evidence(
            {
                "cases": [
                    {
                        "case_id": "c1",
                        "evidence_source": "executor",
                        "execution_receipt": receipt,
                    }
                ]
            }
        )
        self.assertFalse(decision.allowed)

    def test_accepts_sealed_executor_receipt(self) -> None:
        receipt = _seal_receipt()
        self.assertTrue(sealed_executor_receipt(receipt))
        decision = evaluate_certification_evidence(
            {
                "cases": [
                    {
                        "case_id": "c1",
                        "evidence_source": "executor",
                        "execution_receipt": receipt,
                    }
                ]
            }
        )
        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
