#!/usr/bin/env python3
"""Offline, deterministic helper for synthetic sales-management preparation."""

import argparse
import hashlib
import json
import re
import sys
from typing import Any

LIVE_MARKERS = re.compile(r"(?:sk_live|api[_-]?key|password|bearer|\+?\d[\d ()-]{7,})", re.I)
EMAIL_MARKER = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PRIVATE_FIELD_MARKER = re.compile(
    r'"(?:email|phone|telephone|address|account_number|bank_account|ssn|tax_id)"\s*:',
    re.I,
)
ROLLBACK_TARGET = (
    "ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/"
    "tree:9d0be7cedb0fc4ec42bf382735ede36d100f8614"
)
EFFECTS = {"sent": False, "applied": False, "mutated_records": False}


def _owner(request: dict[str, Any]) -> str:
    authority = request.get("authority")
    if isinstance(authority, dict) and isinstance(authority.get("owner"), str) and authority["owner"]:
        return authority["owner"]
    return "consumer_or_principal"


def _result(
    *,
    status: str,
    workflow: str,
    disposition: str,
    rationale: str,
    confidence: str,
    evidence_refs: list[str],
    next_actions: list[str],
    escalation_required: bool,
    escalation_reason: str,
    owner: str,
    idempotency_key: str,
    qualification: str = "needs-evidence",
    priority: str = "unranked",
    handoff_required: bool = False,
    conversion_ref: str | None = None,
) -> dict[str, Any]:
    """Return an output-contract-complete, redacted preparation result."""
    return {
        "status": status,
        "workflow": workflow,
        "decision": {
            "disposition": disposition,
            "rationale": rationale,
            "confidence": confidence,
        },
        "disposition": disposition,
        "idempotency_key": idempotency_key,
        "evidence_refs": evidence_refs,
        "next_actions": next_actions,
        "escalation": {
            "required": escalation_required,
            "reason": escalation_reason,
            "owner": owner,
        },
        "effects": dict(EFFECTS),
        "qualification": {"status": qualification, "basis": evidence_refs},
        "priority": {"level": priority, "basis": []},
        "handoff": {
            "required": handoff_required,
            "recipient": "LiNKclient",
            "conversion_ref": conversion_ref,
            "accepted": False,
        },
        "rollback": ROLLBACK_TARGET,
    }


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted, owner-bound preparation summary without external effects."""
    raw = json.dumps(request, sort_keys=True)
    workflow = request.get("workflow", "unknown")
    if not isinstance(workflow, str) or not workflow:
        workflow = "unknown"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    idempotency_key = f"scm-{digest}"
    owner = _owner(request)
    if (
        LIVE_MARKERS.search(raw)
        or EMAIL_MARKER.search(raw)
        or PRIVATE_FIELD_MARKER.search(raw)
        or request.get("privacy_classification") == "restricted"
    ):
        return _result(
            status="FAILED",
            workflow=workflow,
            disposition="privacy_rejected",
            rationale="Input was rejected by the privacy gate before processing.",
            confidence="high",
            evidence_refs=[],
            next_actions=["Provide synthetic or redacted evidence without credentials or customer data."],
            escalation_required=True,
            escalation_reason="Privacy classification or sensitive content requires owner review.",
            owner=owner,
            idempotency_key=idempotency_key,
        )
    evidence = request.get("source_evidence", [])
    if not isinstance(evidence, list) or not evidence:
        return _result(
            status="FAILED",
            workflow=workflow,
            disposition="needs-evidence",
            rationale="No source evidence was supplied.",
            confidence="unknown",
            evidence_refs=[],
            next_actions=["Supply bounded source evidence and provenance."],
            escalation_required=True,
            escalation_reason="The workflow cannot proceed without source evidence.",
            owner=owner,
            idempotency_key=idempotency_key,
        )
    if any(not isinstance(item, dict) or not item.get("ref") for item in evidence):
        return _result(
            status="FAILED",
            workflow=workflow,
            disposition="needs-evidence",
            rationale="One or more evidence items lacks a stable reference.",
            confidence="unknown",
            evidence_refs=[],
            next_actions=["Supply evidence with stable references and provenance."],
            escalation_required=True,
            escalation_reason="Evidence identity is incomplete.",
            owner=owner,
            idempotency_key=idempotency_key,
        )
    refs = [str(item.get("ref", "")) for item in evidence if isinstance(item, dict) and item.get("ref")]
    disposition = "needs-evidence" if any(item.get("status") == "not_reported" for item in evidence) else "prepared"
    if disposition == "needs-evidence":
        return _result(
            status="PENDING_APPROVAL",
            workflow=workflow,
            disposition=disposition,
            rationale="One or more material signals are not reported.",
            confidence="unknown",
            evidence_refs=refs,
            next_actions=["Owner supplies or confirms the missing evidence."],
            escalation_required=True,
            escalation_reason="Material evidence is incomplete.",
            owner=owner,
            idempotency_key=idempotency_key,
        )
    conversion_ref = request.get("conversion_ref")
    post_conversion = workflow in {"onboarding", "renewal_risk"}
    if post_conversion and not isinstance(conversion_ref, str):
        return _result(
            status="PENDING_APPROVAL",
            workflow=workflow,
            disposition="needs-evidence",
            rationale="Post-conversion work belongs to LiNKclient and requires an evidenced conversion reference for handoff.",
            confidence="high",
            evidence_refs=refs,
            next_actions=["Prepare a LiNKclient handoff with an immutable conversion reference."],
            escalation_required=True,
            escalation_reason="The pre-conversion boundary has been reached without complete handoff evidence.",
            owner="LiNKclient",
            idempotency_key=idempotency_key,
            handoff_required=True,
        )
    if workflow in {"pipeline", "proposal_follow_up", "onboarding", "renewal_risk", "founder_escalation", "other"}:
        status = "PENDING_APPROVAL"
    else:
        status = "COMPLETED"
    priority = "unranked"
    priority_signals = request.get("priority_signals")
    if workflow == "qualification" and isinstance(priority_signals, dict):
        values = [priority_signals.get(name) for name in ("urgency", "impact", "readiness")]
        if all(isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 2 for value in values):
            score = sum(values)
            priority = "high" if score >= 5 else "medium" if score >= 3 else "low"
    return _result(
        status=status,
        workflow=workflow,
        disposition=disposition,
        rationale="Prepared an evidence-bound owner review artifact without external effects.",
        confidence="medium",
        evidence_refs=refs,
        next_actions=["Owner reviews the prepared artifact before any external action."],
        escalation_required=status == "PENDING_APPROVAL",
        escalation_reason="External action remains owner-gated." if status == "PENDING_APPROVAL" else "No external action requested.",
        owner=owner,
        idempotency_key=idempotency_key,
        qualification="qualified" if workflow == "qualification" else "needs-evidence",
        priority=priority,
        handoff_required=post_conversion,
        conversion_ref=conversion_ref if isinstance(conversion_ref, str) else None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a synthetic sales/customer-management summary offline.")
    parser.add_argument("--input", required=True, help="JSON object or path to a JSON fixture")
    args = parser.parse_args()
    try:
        source = args.input
        try:
            with open(source, encoding="utf-8") as handle:
                request = json.load(handle)
        except (FileNotFoundError, OSError):
            request = json.loads(source)
        if not isinstance(request, dict):
            raise ValueError("input must be a JSON object")
        print(json.dumps(normalize_request(request), sort_keys=True, indent=2))
        return 0
    except Exception as exc:  # CLI errors are structured for the caller.
        print(json.dumps({"status": "FAILED", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
