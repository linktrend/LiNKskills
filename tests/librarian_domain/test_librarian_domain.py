#!/usr/bin/env python3
"""Librarian domain worker tests — autonomy boundaries + conformance harness."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "mcp_server",
    REPO_ROOT / "packages" / "client",
    REPO_ROOT / "packages" / "librarian_domain",
    REPO_ROOT / "packages" / "eval_runner",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_librarian.conformance import (  # noqa: E402
    DEFAULT_FIXTURES,
    FakeLibrarianHost,
)
from linkskills_librarian.worker import DomainWorker  # noqa: E402


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


class ConformanceTests(unittest.TestCase):
    def test_fake_host_runs_default_fixtures(self) -> None:
        host = FakeLibrarianHost()
        report = host.run_fixture_suite(DEFAULT_FIXTURES)
        self.assertEqual(report["worker_version"], "0.1")
        staging = report["results"]["propose_improvement_staging_push"]
        self.assertFalse(staging["accepted"])
        self.assertIn("intake_normalize", report["results"])
        self.assertGreaterEqual(report["invocation_count"], 8)


if __name__ == "__main__":
    unittest.main()
