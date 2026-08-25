#!/usr/bin/env python3
"""Offline, deterministic helper for synthetic legal-operations preparation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any

LIVE_MARKERS = re.compile(r"(?:sk_live|api[_-]?key|password|bearer|BEGIN " + r"PRIVATE KEY|customer@example\.com)", re.I)
FORBIDDEN_ACTIONS = {"sign", "accept", "send", "file", "negotiate", "renew", "terminate", "mutate"}
DECLARED_ACTIONS = {"read", "prepare", "compare", *FORBIDDEN_ACTIONS}
ROLLBACK_TARGET = (
    "ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/"
    "tree:9d0be7cedb0fc4ec42bf382735ede36d100f8614"
)
EFFECTS = {"sent": False, "signed": False, "accepted": False, "filed": False, "mutated_records": False}


def _jurisdiction_assessment(request: dict[str, Any]) -> dict[str, str]:
    jurisdiction = request.get("jurisdiction")
    if jurisdiction in (None, "", "unknown", "not_reported"):
        return {"status": "unknown", "basis": "No verified jurisdiction was supplied."}
    return {"status": "supplied_not_verified", "basis": "Jurisdiction was supplied by the owner but applicability remains unverified."}


def _result(
    *,
    request: dict[str, Any],
    digest: str,
    status: str,
    disposition: str,
    rationale: str,
    evidence_refs: list[str],
    next_actions: list[str],
    escalation_required: bool,
    escalation_reason: str,
    escalation_owner: str,
    jurisdiction_assessment: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build the schema-complete, side-effect-free output contract."""
    return {
        "status": status,
        "workflow": request.get("workflow", "other"),
        "decision": {
            "disposition": disposition,
            "rationale": rationale,
            "confidence": "low" if escalation_required else "medium",
            "legal_authority": "not_granted",
        },
        "disposition": disposition,
        "idempotency_key": f"clo-{digest}",
        "evidence_refs": evidence_refs,
        "next_actions": next_actions,
        "escalation": {"required": escalation_required, "reason": escalation_reason, "owner": escalation_owner},
        "jurisdiction_assessment": jurisdiction_assessment or _jurisdiction_assessment(request),
        "effects": dict(EFFECTS),
        "rollback": ROLLBACK_TARGET,
    }


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted preparation summary without legal or external side effects."""
    raw = json.dumps(request, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    if LIVE_MARKERS.search(raw) or request.get("privacy_classification") == "restricted":
        return _result(
            request=request,
            digest=digest,
            status="FAILED",
            disposition="privacy_rejected",
            rationale="Restricted or live-looking material was rejected before evidence processing.",
            evidence_refs=[],
            next_actions=["Submit synthetic or redacted evidence for offline preparation."],
            escalation_required=True,
            escalation_reason="Privacy classification or live-data marker requires owner review.",
            escalation_owner="principal",
            jurisdiction_assessment={"status": "unknown", "basis": "Jurisdiction was not assessed after privacy rejection."},
        )
    evidence = request.get("source_evidence", [])
    refs = [str(item.get("ref", "")) for item in evidence if isinstance(item, dict) and item.get("ref")]
    workflow = request.get("workflow", "other")
    missing = not evidence or any(item.get("status") == "not_reported" for item in evidence if isinstance(item, dict))
    disposition = "needs-evidence" if missing else "prepared"
    requested_raw = request.get("requested_actions", [])
    unknown_actions = (
        not isinstance(requested_raw, list)
        or any(not isinstance(action, str) or action not in DECLARED_ACTIONS for action in requested_raw)
    )
    requested = set(requested_raw) if isinstance(requested_raw, list) and not unknown_actions else set()
    if unknown_actions:
        return _result(
            request=request,
            digest=digest,
            status="PENDING_APPROVAL",
            disposition="authority_escalation",
            rationale="The requested action set contains an undeclared action and was rejected fail-closed.",
            evidence_refs=refs,
            next_actions=["Name only an approved read, prepare, or compare action and obtain Principal approval."],
            escalation_required=True,
            escalation_reason="Unknown requested actions cannot be executed or inferred.",
            escalation_owner="principal",
        )
    if requested & FORBIDDEN_ACTIONS:
        return _result(
            request=request,
            digest=digest,
            status="PENDING_APPROVAL",
            disposition="authority_escalation",
            rationale="The requested action is outside the helper's read-only preparation authority.",
            evidence_refs=refs,
            next_actions=["Route the requested action to a lawyer or Principal; do not execute it here."],
            escalation_required=True,
            escalation_reason="Signing, accepting, sending, filing, negotiating, renewing, terminating, or mutating requires human authority.",
            escalation_owner="lawyer",
        )
    if missing:
        return _result(
            request=request,
            digest=digest,
            status="PENDING_APPROVAL",
            disposition=disposition,
            rationale="Evidence is incomplete or not reported, so no conclusion is prepared.",
            evidence_refs=refs,
            next_actions=["Supply complete provenance and licence fields, then repeat the local review."],
            escalation_required=True,
            escalation_reason="Incomplete evidence cannot support a reliable legal-operations preparation.",
            escalation_owner="lawyer",
        )
    if request.get("jurisdiction") in (None, "", "unknown", "not_reported") or workflow in {"escalation", "playbook_comparison", "other"}:
        return _result(
            request=request,
            digest=digest,
            status="PENDING_APPROVAL",
            disposition=disposition,
            rationale="Preparation is limited by an unverified jurisdiction or an escalation workflow.",
            evidence_refs=refs,
            next_actions=["Have the lawyer or Principal verify jurisdiction and review the prepared evidence."],
            escalation_required=True,
            escalation_reason="Jurisdiction/applicability or legal review remains unresolved.",
            escalation_owner="lawyer",
        )
    return _result(
        request=request,
        digest=digest,
        status="COMPLETED",
        disposition=disposition,
        rationale="Evidence was prepared for the requested read-only workflow; legal authority remains ungranted.",
        evidence_refs=refs,
        next_actions=["Review the prepared summary with the responsible owner; take no external action from this output."],
        escalation_required=False,
        escalation_reason="No external or legal action is performed by this helper.",
        escalation_owner="none",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a synthetic legal-operations summary offline.")
    parser.add_argument("--input", required=True, help="JSON object or path to a JSON fixture")
    args = parser.parse_args()
    try:
        try:
            with open(args.input, encoding="utf-8") as handle:
                request = json.load(handle)
        except (FileNotFoundError, OSError):
            request = json.loads(args.input)
        if not isinstance(request, dict):
            raise ValueError("input must be a JSON object")
        print(json.dumps(normalize_request(request), sort_keys=True, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
