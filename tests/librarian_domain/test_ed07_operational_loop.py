#!/usr/bin/env python3
"""ED-07 Librarian/telemetry worker contract tests."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "librarian_domain"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))
sys.path.insert(0, str(REPO_ROOT))

from linkskills_librarian.telemetry_v2 import (  # noqa: E402
    TelemetryPort,
    opaque_correlation_from,
)
from linkskills_librarian.worker import DomainWorker  # noqa: E402
from global_evaluator import founder_visibility_report, redact_founder_payload  # noqa: E402


def _use_report(**overrides):
    report = {
        "report_kind": "completed_use",
        "score": 9,
        "issue": {"type": "incorrect"},
        "idempotency_key": "ed07-use-1",
        "skill_release_ref": "git-safeguard@1.1.0",
        "skill_version": "1.1.0",
        "skill_digest": "sha256:" + "c" * 64,
        "consumer_class": "cursor",
        "actor_class": "agent_actor",
        "runtime_profile_ref": "cursor-macos",
        "compatibility": "compatible",
        "outcome": "completed",
        "occurred_at": "2026-09-01T00:00:00Z",
        "received_at": "2026-09-01T00:00:01Z",
        "source_fingerprint": "source:ed07",
        "privacy": {"raw_content": False, "prohibited_content": False},
        "retention_class": "minimal",
        "consumer_correlation": "cursor-session-secret-run-99",
        "domain": "linkskills",
    }
    report.update(overrides)
    return report


class Ed07TelemetryContractTests(unittest.TestCase):
    def test_bind_hashes_raw_correlation_and_rejects_forbidden_payload(self) -> None:
        worker = DomainWorker()
        accepted = worker.ingest_use_or_feedback(_use_report())
        self.assertTrue(accepted["accepted"])
        bound = accepted["bound"]
        self.assertEqual(bound["skill_release_ref"], "git-safeguard@1.1.0")
        self.assertEqual(bound["runtime_profile_ref"], "cursor-macos")
        self.assertEqual(
            bound["opaque_correlation"],
            opaque_correlation_from("cursor-session-secret-run-99"),
        )
        self.assertNotIn("consumer_correlation", accepted)
        self.assertNotIn("prompt", accepted)

        rejected = worker.ingest_use_or_feedback(
            _use_report(idempotency_key="ed07-use-bad", metadata={"prompt": "secret"})
        )
        self.assertFalse(rejected["accepted"])
        self.assertEqual(rejected["reason"], "prohibited_content")
        self.assertNotIn("prompt", rejected)

    def test_idempotency_and_retention_purge(self) -> None:
        port = TelemetryPort()
        first = port.submit(_use_report())
        self.assertEqual(first, port.submit(_use_report()))
        conflict = _use_report(score=8)
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            port.submit(conflict)
        before = port.purge(now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        self.assertEqual(before["purged_events"], 0)
        after = port.purge(now=datetime(2026, 9, 10, tzinfo=timezone.utc))
        self.assertEqual(after["purged_events"], 1)
        self.assertEqual(after["retained"], 0)

    def test_cross_domain_and_cardinality_overflow(self) -> None:
        worker = DomainWorker()
        brain = worker.ingest_use_or_feedback(_use_report(domain="linkbrain"))
        self.assertFalse(brain["accepted"])
        self.assertEqual(brain["reason"], "cross_domain_rejected")

        port = TelemetryPort(max_cardinality=1)
        port.submit(_use_report())
        port.submit(_use_report(idempotency_key="ed07-use-2", consumer_class="codex"))
        aggregate = port.aggregate()
        self.assertEqual(len(aggregate), 2)
        self.assertIn(("*", "*", "*", "*", "*", "overflow"), aggregate)


class Ed07WorkerLoopTests(unittest.TestCase):
    def test_prompt_only_supervised_run_cannot_certify(self) -> None:
        worker = DomainWorker()
        worker.enqueue_job(
            {
                "kind": "interpret_eval",
                "payload": {
                    "prompt_only": True,
                    "evidence": {"passed": True, "case_results": [{"id": "c1", "passed": True}]},
                },
            }
        )
        run = worker.supervised_run({"domain": "linkskills"})
        self.assertTrue(run["accepted"])
        result = run["processed"][0]["result"]
        self.assertFalse(result["certifying"])
        self.assertEqual(result["recommendation"], "hold_eval_pending")

    def test_disable_retry_dlq_and_recovery(self) -> None:
        worker = DomainWorker(max_retries=2)
        worker.enqueue_job(
            {
                "job_id": "job-bad",
                "kind": "ingest",
                "payload": _use_report(domain="linkbrain"),
            }
        )
        first = worker.retry_job({"job_id": "job-bad"})
        self.assertEqual(first["outcome"], "retry")
        second = worker.retry_job({"job_id": "job-bad"})
        self.assertEqual(second["outcome"], "dead_letter")
        self.assertEqual(len(worker.dead_letter), 1)

        disabled = worker.disable({})
        self.assertFalse(disabled["enabled"])
        self.assertTrue(disabled["queue_preserved"])
        refused = worker.ingest_use_or_feedback(_use_report(idempotency_key="after-disable"))
        self.assertEqual(refused["reason"], "worker_disabled")
        recovered = worker.recover({"replay_dlq": True})
        self.assertTrue(recovered["enabled"])
        self.assertEqual(recovered["restored_from_dlq"], 1)
        self.assertEqual(recovered["dlq_depth"], 0)

    def test_status_report_separates_proof_classes(self) -> None:
        worker = DomainWorker()
        worker.ingest_use_or_feedback(_use_report())
        status = worker.status_report({})
        self.assertEqual(status["worker_version"], "0.2")
        self.assertEqual(status["proof_classes"]["worker_contract"]["status"], "pass")
        self.assertEqual(status["proof_classes"]["production"]["status"], "hold")
        self.assertTrue(status["redacted"])
        founder = founder_visibility_report(status)
        self.assertEqual(founder["proof_classes"]["source"]["status"], "pass")
        self.assertNotIn("prompt", redact_founder_payload({"prompt": "nope", "score": 1}))


if __name__ == "__main__":
    unittest.main()
