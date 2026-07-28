"""Fake host harness for DomainWorker v0.1 conformance fixtures."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional

from .worker import DomainWorker


class FakeLibrarianHost:
    """Minimal stand-in for LiNKplatform librarian-runner invocation."""

    def __init__(self, worker: Optional[DomainWorker] = None) -> None:
        self.worker = worker or DomainWorker()
        self.invocations: List[Dict[str, Any]] = []

    def invoke(self, method: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        if not hasattr(self.worker, method):
            raise AttributeError(f"Unknown worker method: {method}")
        fn: Callable[[Mapping[str, Any]], Dict[str, Any]] = getattr(self.worker, method)
        self.invocations.append({"method": method, "payload": dict(payload)})
        return fn(payload)

    def run_fixture_suite(self, fixtures: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for name, fixture in fixtures.items():
            method = str(fixture.get("method") or name)
            payload = fixture.get("payload") or {}
            results[name] = self.invoke(method, payload if isinstance(payload, Mapping) else {})
        return {
            "worker_version": self.worker.version,
            "results": results,
            "invocation_count": len(self.invocations),
        }


DEFAULT_FIXTURES: Dict[str, Dict[str, Any]] = {
    "intake_normalize": {
        "method": "intake_normalize",
        "payload": {
            "skill_ref": "git-safeguard",
            "provenance": {"source": "catalog", "commit": "deadbeef"},
        },
    },
    "prioritize": {
        "method": "prioritize",
        "payload": {
            "candidates": [
                {"skill_id": "a", "impact": 0.2, "cost": 1.0},
                {"skill_id": "b", "impact": 0.9, "cost": 2.0},
            ]
        },
    },
    "propose_improvement_ok": {
        "method": "propose_improvement",
        "payload": {
            "skill_id": "git-safeguard",
            "summary": "clarify branch checks",
            "target_branch": "feature/librarian-git-safeguard",
            "action": "open_pr",
        },
    },
    "propose_improvement_staging_push": {
        "method": "propose_improvement",
        "payload": {
            "skill_id": "git-safeguard",
            "summary": "illegal staging push",
            "target_branch": "staging",
            "action": "push_staging",
            "push_to_staging": True,
        },
    },
    "request_eval": {
        "method": "request_eval",
        "payload": {
            "skill_id": "git-safeguard",
            "execution_profile": "cursor-macos",
            "eval_suite_ref": "skills/git-safeguard/references/eval-suite.yaml",
        },
    },
    "interpret_eval_evidence": {
        "method": "interpret_eval_evidence",
        "payload": {
            # Intentionally thin — must NOT certify without sealed executor receipts.
            "evidence": {
                "passed": True,
                "case_results": [{"id": "c1", "passed": True}],
            }
        },
    },
    "propose_consolidation_low_confidence": {
        "method": "propose_consolidation",
        "payload": {
            "kind": "merge",
            "confidence": 0.2,
            "skills": ["a", "b"],
            "summary": "possible duplicate",
        },
    },
    "enqueue_review": {
        "method": "enqueue_review",
        "payload": {"kind": "manual", "note": "fixture"},
    },
}
