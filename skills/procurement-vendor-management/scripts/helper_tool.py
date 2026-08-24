#!/usr/bin/env python3
"""Offline, deterministic helper for synthetic procurement preparation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any

LIVE_MARKERS = re.compile(r"(?:sk_live|api[_-]?key|password|bearer|BEGIN " + r"PRIVATE KEY)", re.I)
PRIVATE_FIELD_MARKER = re.compile(r'"(?:bank|account|routing|tax_id|personal_id|phone|email|address)"\s*:', re.I)
FORBIDDEN_ACTIONS = {"approve", "order", "accept", "send", "negotiate", "renew", "terminate", "mutate"}
DECLARED_ACTIONS = {"read", "prepare", "compare", *FORBIDDEN_ACTIONS}
ROLLBACK_TARGET = "ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/tree:9d0be7cedb0fc4ec42bf382735ede36d100f8614"
EFFECTS = {"sent": False, "accepted": False, "ordered": False, "mutated_records": False}


def _result(*, request: dict[str, Any], digest: str, status: str, disposition: str, rationale: str, confidence: str, refs: list[str], next_actions: list[str], escalation: bool, reason: str, owner: str) -> dict[str, Any]:
    """Return a complete redacted output contract without external effects."""
    return {
        "status": status,
        "workflow": request.get("workflow", "other"),
        "decision": {"disposition": disposition, "rationale": rationale, "confidence": confidence},
        "disposition": disposition,
        "idempotency_key": f"pvm-{digest}",
        "evidence_refs": refs,
        "next_actions": next_actions,
        "escalation": {"required": escalation, "reason": reason, "owner": owner},
        "effects": dict(EFFECTS),
        "rollback": ROLLBACK_TARGET,
    }


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Prepare a synthetic procurement result and fail closed on unsafe input."""
    raw = json.dumps(request, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    if LIVE_MARKERS.search(raw) or PRIVATE_FIELD_MARKER.search(raw) or request.get("privacy_classification") == "restricted":
        return _result(request=request, digest=digest, status="FAILED", disposition="privacy_rejected", rationale="Restricted or sensitive procurement material was rejected before processing.", confidence="high", refs=[], next_actions=["Supply synthetic or redacted evidence without credentials or private vendor data."], escalation=True, reason="Privacy gate requires consumer-owner review.", owner="consumer_owner")
    evidence = request.get("source_evidence", [])
    if not isinstance(evidence, list) or not evidence:
        return _result(request=request, digest=digest, status="FAILED", disposition="needs-evidence", rationale="No source evidence was supplied.", confidence="unknown", refs=[], next_actions=["Supply evidence references with provenance and licence."], escalation=True, reason="Procurement claims cannot be prepared without evidence.", owner="consumer_owner")
    if any(not isinstance(item, dict) or not item.get("ref") for item in evidence):
        return _result(request=request, digest=digest, status="FAILED", disposition="needs-evidence", rationale="Evidence identity is incomplete.", confidence="unknown", refs=[], next_actions=["Supply stable evidence references and provenance."], escalation=True, reason="Every evidence item needs a stable reference.", owner="consumer_owner")
    refs = [str(item["ref"]) for item in evidence]
    requested_raw = request.get("requested_actions", [])
    unknown = not isinstance(requested_raw, list) or any(not isinstance(action, str) or action not in DECLARED_ACTIONS for action in requested_raw)
    if unknown:
        return _result(request=request, digest=digest, status="PENDING_APPROVAL", disposition="authority_escalation", rationale="An undeclared requested action was rejected fail-closed.", confidence="low", refs=refs, next_actions=["Name only read, prepare, or compare and obtain consumer-owner approval for any effect."], escalation=True, reason="Unknown actions cannot be inferred or executed.", owner="consumer_owner")
    requested = set(requested_raw)
    if requested & FORBIDDEN_ACTIONS or request.get("workflow") in {"approval_brief", "continuity_risk", "other"}:
        return _result(request=request, digest=digest, status="PENDING_APPROVAL", disposition="authority_escalation" if requested & FORBIDDEN_ACTIONS else "prepared", rationale="The request requires consumer-owner review before any commitment or unresolved risk decision.", confidence="low", refs=refs, next_actions=["Review the evidence and approve a bounded next action outside this provider."], escalation=True, reason="Spending, acceptance, supplier commitment, or material continuity risk remains owner-gated.", owner="consumer_owner")
    if any(item.get("status") == "not_reported" for item in evidence):
        return _result(request=request, digest=digest, status="PENDING_APPROVAL", disposition="needs-evidence", rationale="One or more material procurement signals are not reported.", confidence="unknown", refs=refs, next_actions=["Supply or confirm the missing pricing, term, performance, or continuity evidence."], escalation=True, reason="Incomplete evidence cannot support a supplier decision.", owner="consumer_owner")
    return _result(request=request, digest=digest, status="COMPLETED", disposition="prepared", rationale="Evidence-bound procurement preparation completed without selecting a supplier or applying an external effect.", confidence="medium", refs=refs, next_actions=["Consumer owner reviews the prepared artifact before any commitment."], escalation=False, reason="No external action is performed by this helper.", owner="none")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a synthetic procurement summary offline.")
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
