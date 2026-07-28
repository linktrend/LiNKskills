#!/usr/bin/env python3
"""Librarian domain worker tests — autonomy boundaries + conformance harness."""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "mcp_server",
    REPO_ROOT / "packages" / "client",
    REPO_ROOT / "packages" / "librarian_domain",
    REPO_ROOT / "packages" / "eval_runner",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_core.certification import sealed_executor_receipt  # noqa: E402
from linkskills_librarian.conformance import (  # noqa: E402
    DEFAULT_FIXTURES,
    FakeLibrarianHost,
)
from linkskills_librarian.worker import DomainWorker  # noqa: E402


def _seal_receipt(**overrides):
    base = {
        "receipt_id": "rcpt-lib-1",
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
        "executor_version": "linkskills-eval-executor/0.2.0",
        "evidence_source": "executor",
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
    assert sealed_executor_receipt(base)
    return base


class WorkerPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.worker = DomainWorker()

    def test_refuses_staging_push_proposal(self) -> None:
        result = self.worker.propose_improvement(
            {
                "skill_id": "git-safeguard",
                "summary": "ship it",
                "action": "push_staging",
                "target_branch": "staging",
                "push_to_staging": True,
            }
        )
        self.assertFalse(result["accepted"])
        self.assertEqual(result["policy"]["code"], "policy_refuse_protected_push")
        self.assertIsNone(result["proposal"])

    def test_refuses_main_push_flag(self) -> None:
        result = self.worker.propose_improvement(
            {
                "skill_id": "git-safeguard",
                "action": "open_pr",
                "target_branch": "feature/ok",
                "push_to_main": True,
            }
        )
        self.assertFalse(result["accepted"])
        self.assertEqual(result["policy"]["code"], "policy_refuse_protected_push")

    def test_allows_feature_branch_pr(self) -> None:
        result = self.worker.propose_improvement(
            {
                "skill_id": "git-safeguard",
                "action": "open_pr",
                "target_branch": "feature/librarian-improve",
                "summary": "ok",
            }
        )
        self.assertTrue(result["accepted"])
        self.assertTrue(result["proposal"]["direct_push_forbidden"])

    def test_low_confidence_consolidation_escalates(self) -> None:
        result = self.worker.propose_consolidation(
            {
                "kind": "merge",
                "confidence": 0.1,
                "skills": ["a", "b"],
            }
        )
        self.assertFalse(result["accepted"])
        self.assertTrue(result["escalate"])
        self.assertEqual(result["policy"]["code"], "policy_escalate_low_confidence")

    def test_thin_case_results_never_certify(self) -> None:
        result = self.worker.interpret_eval_evidence(
            {
                "evidence": {
                    "passed": True,
                    "case_results": [{"id": "c1", "passed": True, "output": "fabricated"}],
                }
            }
        )
        self.assertFalse(result["certifying"])
        self.assertEqual(result["recommendation"], "hold_eval_pending")

    def test_sealed_receipts_can_certify(self) -> None:
        receipt = _seal_receipt()
        result = self.worker.interpret_eval_evidence(
            {
                "evidence": {
                    "passed": True,
                    "case_results": [
                        {
                            "case_id": "c1",
                            "evidence_source": "executor",
                            "execution_receipt": receipt,
                        }
                    ],
                }
            }
        )
        self.assertTrue(result["certifying"])
        self.assertEqual(result["recommendation"], "promote")


class ConformanceTests(unittest.TestCase):
    def test_fake_host_runs_default_fixtures(self) -> None:
        host = FakeLibrarianHost()
        report = host.run_fixture_suite(DEFAULT_FIXTURES)
        self.assertEqual(report["worker_version"], "0.1")
        staging = report["results"]["propose_improvement_staging_push"]
        self.assertFalse(staging["accepted"])
        thin = report["results"]["interpret_eval_evidence"]
        self.assertFalse(thin["certifying"])
        self.assertIn("intake_normalize", report["results"])
        self.assertGreaterEqual(report["invocation_count"], 8)


if __name__ == "__main__":
    unittest.main()
