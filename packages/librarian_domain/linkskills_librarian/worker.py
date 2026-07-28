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


WORKER_VERSION = "0.1"
DOMAIN_KEY = "linkskills"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class DomainWorker:
    """Skills-domain Librarian worker (contract v0.1 method surface)."""

    version: str = WORKER_VERSION
    domain_key: str = DOMAIN_KEY
    review_queue: List[Dict[str, Any]] = field(default_factory=list)
    store: Optional[ReviewQueueStore] = None
    store_path: Optional[str] = None

    def __post_init__(self) -> None:
        if self.store is None and self.store_path:
            self.store = open_review_queue_store(store_path=Path(self.store_path))

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
