"""Versioned LiNKskills Librarian DomainWorker v0.1.

Host integration lives in LiNKplatform; this package owns domain methods only.
Do NOT edit LiNKplatform from this worker.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from linkskills_core.certification import evaluate_certification_evidence

from .policies import (
    evaluate_proposal,
    first_blocking,
    refuse_protected_branch_push,
)
from .store import ReviewQueueStore, open_review_queue_store
from .telemetry_v2 import (
    ALLOWED_DOMAINS,
    CROSS_DOMAIN,
    TelemetryPort,
    bind_use_or_feedback_report,
    classification,
)


WORKER_VERSION = "0.2"
CONFORMANCE_PACKAGE = "linkskills-librarian-conformance/0.2"
DOMAIN_KEY = "linkskills"
MAX_JOB_RETRIES = 3
EXTERNAL_REVIEW_OUTCOMES = frozenset({"accept", "adapt", "postpone", "reject"})
EXTERNAL_REVIEW_EVIDENCE = frozenset(
    {"diff", "license", "security", "compatibility", "evaluation", "customization", "feedback"}
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class DomainWorker:
    """Skills-domain Librarian worker (contract v0.2 method surface)."""

    version: str = WORKER_VERSION
    domain_key: str = DOMAIN_KEY
    conformance_package: str = CONFORMANCE_PACKAGE
    review_queue: List[Dict[str, Any]] = field(default_factory=list)
    store: Optional[ReviewQueueStore] = None
    store_path: Optional[str] = None
    telemetry: Optional[TelemetryPort] = None
    enabled: bool = True
    jobs: List[Dict[str, Any]] = field(default_factory=list)
    dead_letter: List[Dict[str, Any]] = field(default_factory=list)
    max_retries: int = MAX_JOB_RETRIES

    def __post_init__(self) -> None:
        if self.store is None and self.store_path:
            self.store = open_review_queue_store(store_path=Path(self.store_path))
        if self.telemetry is None:
            self.telemetry = TelemetryPort()

    def intake_normalize(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        skill_ref = str(payload.get("skill_ref") or payload.get("skill_id") or "")
        provenance = payload.get("provenance") or {}
        gaps: List[str] = []
        if not skill_ref:
            gaps.append("missing_skill_ref")
        if not provenance:
            gaps.append("missing_provenance")
        return {
            "worker_version": self.version,
            "operation": "intake_normalize",
            "skill_ref": skill_ref,
            "normalized": {
                "schema_version": "0.1",
                "skill_id": skill_ref,
                "pack_mapping": {
                    "identity": bool(skill_ref),
                    "routing": "pending",
                    "execution_contract": "pending",
                    "typed_dependencies": "pending",
                },
                "provenance": dict(provenance),
            },
            "gaps": gaps,
            "overlap_notes": list(payload.get("overlap_notes") or []),
            "at": _utc_now(),
        }

    def prioritize(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        candidates = list(payload.get("candidates") or [])
        ranked = sorted(
            candidates,
            key=lambda item: (
                -float(item.get("impact") or 0.0),
                float(item.get("cost") or 0.0),
                str(item.get("skill_id") or ""),
            ),
        )
        return {
            "worker_version": self.version,
            "operation": "prioritize",
            "prioritized": ranked,
            "count": len(ranked),
            "at": _utc_now(),
        }

    def propose_improvement(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        proposal = {
            "action": payload.get("action") or "open_pr",
            "target_branch": payload.get("target_branch") or payload.get("branch") or "feature/librarian",
            "skill_id": payload.get("skill_id"),
            "summary": payload.get("summary") or "proposed improvement",
            "push_to_staging": bool(payload.get("push_to_staging")),
            "push_to_main": bool(payload.get("push_to_main")),
            "grant_permissions": bool(payload.get("grant_permissions")),
            "confidence": payload.get("confidence"),
        }
        # Hard refuse staging/main push proposals.
        branch_decision = refuse_protected_branch_push(proposal=proposal, action=proposal["action"])
        decisions = evaluate_proposal(proposal)
        blocking = first_blocking([branch_decision, *decisions])
        if blocking is not None:
            return {
                "worker_version": self.version,
                "operation": "propose_improvement",
                "accepted": False,
                "proposal": None,
                "policy": blocking.to_dict(),
                "at": _utc_now(),
            }
        return {
            "worker_version": self.version,
            "operation": "propose_improvement",
            "accepted": True,
            "proposal": {
                "proposal_id": str(uuid.uuid4()),
                "branch": proposal["target_branch"],
                "skill_id": proposal["skill_id"],
                "summary": proposal["summary"],
                "pr_required": True,
                "direct_push_forbidden": True,
            },
            "policy": {"allowed": True, "code": "ok"},
            "at": _utc_now(),
        }

    def request_eval(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        skill_id = str(payload.get("skill_id") or "")
        profile = str(payload.get("execution_profile") or "default")
        suite_ref = str(payload.get("eval_suite_ref") or "")
        return {
            "worker_version": self.version,
            "operation": "request_eval",
            "request_id": str(uuid.uuid4()),
            "skill_id": skill_id,
            "execution_profile": profile,
            "eval_suite_ref": suite_ref,
            "status": "queued",
            "requires_executed_evidence": True,
            "at": _utc_now(),
        }

    def interpret_eval_evidence(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Interpret eval evidence using the same receipt-bound rules as Eval Runner.

        Non-empty ``case_results`` alone never certifies — sealed executor
        receipts are required via ``evaluate_certification_evidence``.
        """
        evidence = dict(payload.get("evidence") or {})
        if payload.get("prompt_only"):
            evidence["prompt_only"] = True
        decision = evaluate_certification_evidence(evidence)
        if not decision.allowed:
            return {
                "worker_version": self.version,
                "operation": "interpret_eval_evidence",
                "certifying": False,
                "recommendation": "hold_eval_pending",
                "reason": decision.reason,
                "at": _utc_now(),
            }
        passed = bool(evidence.get("passed"))
        return {
            "worker_version": self.version,
            "operation": "interpret_eval_evidence",
            "certifying": bool(passed),
            "recommendation": "promote" if passed else "demote_or_hold",
            "passed": passed,
            "evidence_decision": decision.reason,
            "at": _utc_now(),
        }

    def propose_consolidation(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        proposal = {
            "kind": payload.get("kind") or "merge",
            "action": "propose_consolidation",
            "confidence": payload.get("confidence"),
            "skills": list(payload.get("skills") or []),
            "summary": payload.get("summary") or "consolidation proposal",
        }
        decisions = evaluate_proposal(proposal)
        blocking = first_blocking(decisions)
        if blocking is not None:
            review = self.enqueue_review(
                {
                    "kind": "consolidation_escalation",
                    "proposal": proposal,
                    "policy": blocking.to_dict(),
                }
            )
            return {
                "worker_version": self.version,
                "operation": "propose_consolidation",
                "accepted": False,
                "escalate": True,
                "policy": blocking.to_dict(),
                "review": review,
                "at": _utc_now(),
            }
        return {
            "worker_version": self.version,
            "operation": "propose_consolidation",
            "accepted": True,
            "proposal": {
                "proposal_id": str(uuid.uuid4()),
                "kind": proposal["kind"],
                "skills": proposal["skills"],
                "summary": proposal["summary"],
                "confidence": proposal["confidence"],
            },
            "at": _utc_now(),
        }

    def enqueue_review(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        item = {
            "review_id": str(uuid.uuid4()),
            "kind": payload.get("kind") or "general",
            "payload": dict(payload),
            "status": "queued",
            "at": _utc_now(),
        }
        self.review_queue.append(item)
        if self.store is not None:
            self.store.enqueue(item)
        return {
            "worker_version": self.version,
            "operation": "enqueue_review",
            "item": item,
            "queue_depth": self.store.depth() if self.store is not None else len(self.review_queue),
            "at": _utc_now(),
        }

    def review_update_candidate(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Record a bounded external-candidate recommendation.

        The Librarian domain can recommend an outcome, but it cannot qualify a
        release, apply a migration, or move a live pointer.  Platform receipts
        are required for those actions.
        """
        candidate_id = str(payload.get("candidate_id") or "").strip()
        outcome = str(payload.get("outcome") or "").strip().lower()
        reviewer = str(payload.get("reviewer") or "").strip()
        evidence = dict(payload.get("evidence") or {})
        if not candidate_id:
            raise ValueError("missing_candidate_id")
        if outcome not in EXTERNAL_REVIEW_OUTCOMES:
            raise ValueError("invalid_review_outcome")
        if not reviewer:
            raise ValueError("missing_reviewer")
        missing = sorted(EXTERNAL_REVIEW_EVIDENCE.difference(evidence))
        if missing:
            raise ValueError("missing_review_evidence:" + ",".join(missing))
        review_id = str(payload.get("review_id") or f"review:{candidate_id}")
        status = {
            "accept": "accepted_pending_platform",
            "adapt": "adaptation_pending_platform",
            "postpone": "postponed",
            "reject": "rejected",
        }[outcome]
        return {
            "worker_version": self.version,
            "operation": "review_update_candidate",
            "review_id": review_id,
            "candidate_id": candidate_id,
            "outcome": outcome,
            "status": status,
            "evidence": evidence,
            "reviewer": reviewer,
            "platform_apply_required": outcome in {"accept", "adapt"},
            "direct_activation": False,
            "at": _utc_now(),
        }

    def _disabled_response(self, operation: str) -> Dict[str, Any]:
        return {
            "worker_version": self.version,
            "operation": operation,
            "accepted": False,
            "reason": "worker_disabled",
            "enabled": False,
            "queue_preserved": True,
            "queue_depth": self.store.depth() if self.store is not None else len(self.review_queue),
            "job_depth": len(self.jobs),
            "dlq_depth": len(self.dead_letter),
            "at": _utc_now(),
        }

    def _domain_of(self, payload: Mapping[str, Any]) -> str:
        return str(payload.get("domain") or payload.get("domain_key") or self.domain_key).strip().lower()

    def _reject_cross_domain(self, operation: str, payload: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        domain = self._domain_of(payload)
        if domain in CROSS_DOMAIN or domain not in ALLOWED_DOMAINS:
            return {
                "worker_version": self.version,
                "operation": operation,
                "accepted": False,
                "reason": "cross_domain_rejected",
                "domain": domain,
                "at": _utc_now(),
            }
        return None

    def ingest_use_or_feedback(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Accept a bounded use or feedback report bound to exact release/profile."""
        if not self.enabled:
            return self._disabled_response("ingest_use_or_feedback")
        blocked = self._reject_cross_domain("ingest_use_or_feedback", payload)
        if blocked is not None:
            return blocked
        assert self.telemetry is not None
        try:
            bound = bind_use_or_feedback_report(payload)
            receipt = self.telemetry.submit(bound)
        except ValueError as exc:
            return {
                "worker_version": self.version,
                "operation": "ingest_use_or_feedback",
                "accepted": False,
                "reason": str(exc),
                "at": _utc_now(),
            }
        return {
            "worker_version": self.version,
            "operation": "ingest_use_or_feedback",
            "accepted": bool(receipt.get("accepted")),
            "receipt": receipt,
            "bound": {
                "skill_release_ref": receipt.get("skill_release_ref"),
                "runtime_profile_ref": receipt.get("runtime_profile_ref"),
                "skill_digest": receipt.get("skill_digest"),
                "opaque_correlation": receipt.get("opaque_correlation"),
            }
            if receipt.get("accepted")
            else None,
            "reason": receipt.get("reason"),
            "at": _utc_now(),
        }

    def diagnose_performance(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Return redacted improvement candidates from bounded telemetry aggregates."""
        if not self.enabled:
            return self._disabled_response("diagnose_performance")
        blocked = self._reject_cross_domain("diagnose_performance", payload)
        if blocked is not None:
            return blocked
        assert self.telemetry is not None
        aggregates = self.telemetry.aggregate()
        candidates: List[Dict[str, Any]] = []
        for dims, count in aggregates.items():
            issue_type = dims[5]
            if issue_type in {"none", "overflow"}:
                continue
            candidates.append(
                {
                    "skill_release_ref": dims[0],
                    "consumer_class": dims[1],
                    "actor_class": dims[2],
                    "runtime_profile_ref": dims[3],
                    "compatibility": dims[4],
                    "issue_type": issue_type,
                    "count": count,
                    "classification": classification(issue_type),
                }
            )
        candidates.sort(key=lambda item: (-int(item["count"]), str(item["skill_release_ref"])))
        return {
            "worker_version": self.version,
            "operation": "diagnose_performance",
            "candidates": candidates,
            "cardinality": len(aggregates),
            "at": _utc_now(),
        }

    def enqueue_job(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Enqueue a Skills-only operational job with retry/DLQ metadata."""
        if not self.enabled:
            return self._disabled_response("enqueue_job")
        blocked = self._reject_cross_domain("enqueue_job", payload)
        if blocked is not None:
            return blocked
        job = {
            "job_id": str(payload.get("job_id") or uuid.uuid4()),
            "kind": str(payload.get("kind") or "ingest"),
            "status": "queued",
            "attempt": 0,
            "payload": dict(payload.get("payload") or payload),
            "last_error": None,
            "at": _utc_now(),
        }
        self.jobs.append(job)
        return {
            "worker_version": self.version,
            "operation": "enqueue_job",
            "job": job,
            "job_depth": len(self.jobs),
            "at": _utc_now(),
        }

    def _fail_job(self, job: Dict[str, Any], reason: str) -> Dict[str, Any]:
        job["attempt"] = int(job.get("attempt") or 0) + 1
        job["last_error"] = reason
        if job["attempt"] >= self.max_retries:
            job["status"] = "dead_letter"
            self.dead_letter.append(dict(job))
            return {"outcome": "dead_letter", "job": dict(job)}
        job["status"] = "retry"
        return {"outcome": "retry", "job": dict(job)}

    def retry_job(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Retry one queued/retry job; exhausted attempts move to the DLQ."""
        if not self.enabled:
            return self._disabled_response("retry_job")
        job_id = str(payload.get("job_id") or "")
        job = next((item for item in self.jobs if item.get("job_id") == job_id), None)
        if job is None:
            return {
                "worker_version": self.version,
                "operation": "retry_job",
                "accepted": False,
                "reason": "unknown_job",
                "at": _utc_now(),
            }
        result = self._execute_job(job)
        return {
            "worker_version": self.version,
            "operation": "retry_job",
            "accepted": result.get("outcome") != "dead_letter",
            **result,
            "at": _utc_now(),
        }

    def _execute_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        kind = str(job.get("kind") or "ingest")
        inner = dict(job.get("payload") or {})
        if kind in {"ingest", "use", "feedback"}:
            result = self.ingest_use_or_feedback(inner)
            if result.get("accepted"):
                job["status"] = "done"
                return {"outcome": "done", "job": dict(job), "result": result}
            return self._fail_job(job, str(result.get("reason") or "ingest_rejected"))
        if kind == "interpret_eval":
            result = self.interpret_eval_evidence(inner)
            if result.get("certifying") is False and inner.get("prompt_only"):
                job["status"] = "done"
                return {"outcome": "done", "job": dict(job), "result": result}
            if result.get("certifying") or result.get("recommendation"):
                job["status"] = "done"
                return {"outcome": "done", "job": dict(job), "result": result}
            return self._fail_job(job, str(result.get("reason") or "eval_unusable"))
        return self._fail_job(job, "unknown_job_kind")

    def supervised_run(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Process queued Skills evidence only; never certifies from prompt-only input."""
        if not self.enabled:
            return self._disabled_response("supervised_run")
        blocked = self._reject_cross_domain("supervised_run", payload)
        if blocked is not None:
            return blocked
        processed: List[Dict[str, Any]] = []
        for job in list(self.jobs):
            if job.get("status") not in {"queued", "retry"}:
                continue
            processed.append(self._execute_job(job))
        assert self.telemetry is not None
        return {
            "worker_version": self.version,
            "operation": "supervised_run",
            "accepted": True,
            "processed": processed,
            "job_depth": len([j for j in self.jobs if j.get("status") in {"queued", "retry"}]),
            "dlq_depth": len(self.dead_letter),
            "prompt_only_cannot_certify": True,
            "skills_only": True,
            "metrics": {
                ",".join(key): count for key, count in self.telemetry.aggregate().items()
            },
            "at": _utc_now(),
        }

    def disable(self, payload: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        """Independently disable the Skills worker while preserving queue and evidence."""
        del payload
        self.enabled = False
        return {
            "worker_version": self.version,
            "operation": "disable",
            "enabled": False,
            "queue_preserved": True,
            "queue_depth": self.store.depth() if self.store is not None else len(self.review_queue),
            "job_depth": len(self.jobs),
            "dlq_depth": len(self.dead_letter),
            "at": _utc_now(),
        }

    def recover(self, payload: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        """Re-enable the worker without replaying the DLQ unless asked."""
        replay_dlq = bool((payload or {}).get("replay_dlq"))
        self.enabled = True
        restored = 0
        if replay_dlq:
            for item in list(self.dead_letter):
                item["status"] = "retry"
                item["attempt"] = 0
                self.jobs.append(item)
                restored += 1
            self.dead_letter.clear()
        return {
            "worker_version": self.version,
            "operation": "recover",
            "enabled": True,
            "replay_dlq": replay_dlq,
            "restored_from_dlq": restored,
            "job_depth": len(self.jobs),
            "dlq_depth": len(self.dead_letter),
            "at": _utc_now(),
        }

    def purge_telemetry(self, payload: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        """Apply retention windows and drop expired telemetry receipts."""
        assert self.telemetry is not None
        now_raw = (payload or {}).get("now")
        now = None
        if isinstance(now_raw, str) and now_raw:
            text = now_raw[:-1] + "+00:00" if now_raw.endswith("Z") else now_raw
            now = datetime.fromisoformat(text)
        result = self.telemetry.purge(now=now)
        return {
            "worker_version": self.version,
            "operation": "purge_telemetry",
            **result,
            "at": _utc_now(),
        }

    def status_report(self, payload: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        """Founder-facing Skills status with separated proof classes and no payloads."""
        del payload
        assert self.telemetry is not None
        aggregates = self.telemetry.aggregate()
        backlog = self.store.list_queue(status="queued") if self.store is not None else [
            item for item in self.review_queue if item.get("status") == "queued"
        ]
        return {
            "worker_version": self.version,
            "conformance_package": self.conformance_package,
            "domain_key": self.domain_key,
            "operation": "status_report",
            "enabled": self.enabled,
            "backlog": {
                "review_queued": len(backlog),
                "jobs_open": len([j for j in self.jobs if j.get("status") in {"queued", "retry"}]),
                "dead_letter": len(self.dead_letter),
            },
            "metrics_cardinality": len(aggregates),
            "metrics": {",".join(key): count for key, count in aggregates.items()},
            "proof_classes": {
                "source": {
                    "status": "pass",
                    "claim": "versioned Skills worker and conformance package exist in source",
                },
                "qualification": {
                    "status": "hold",
                    "claim": "live qualification remains ED-03/ED-04 evidence; this packet does not re-certify",
                },
                "selectability": {
                    "status": "hold",
                    "claim": "channel pointers and consumer activation are out of ED-07 source scope",
                },
                "consumer": {
                    "status": "hold",
                    "claim": "consumer config and live host integration are prohibited in this packet",
                },
                "server": {
                    "status": "hold",
                    "claim": "no deploy or live host mutation",
                },
                "production": {
                    "status": "hold",
                    "claim": "supervised production-equivalent run is source-simulated; live host waits XP-01",
                },
                "worker_contract": {
                    "status": "pass",
                    "claim": "use/feedback bind, privacy, retention, disable/retry/DLQ, prompt-only refusal",
                },
            },
            "redacted": True,
            "at": _utc_now(),
        }
