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
    " (no prior qualified PKT-16 release)"
)


def _failure(disposition: str, workflow: str = "unknown") -> dict[str, Any]:
    """Return a redacted terminal result with every external effect disabled."""
    return {
        "status": "FAILED",
        "workflow": workflow,
        "disposition": disposition,
        "effects": {"sent": False, "applied": False, "mutated_records": False},
        "rollback": ROLLBACK_TARGET,
    }


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted, owner-bound preparation summary without external effects."""
    raw = json.dumps(request, sort_keys=True)
    workflow = request.get("workflow", "unknown")
    if not isinstance(workflow, str) or not workflow:
        workflow = "unknown"
    if (
        LIVE_MARKERS.search(raw)
        or EMAIL_MARKER.search(raw)
        or PRIVATE_FIELD_MARKER.search(raw)
        or request.get("privacy_classification") == "restricted"
    ):
        return _failure("privacy_rejected", workflow)
    evidence = request.get("source_evidence", [])
    if not isinstance(evidence, list) or not evidence:
        return _failure("needs-evidence", workflow)
    if any(not isinstance(item, dict) or not item.get("ref") for item in evidence):
        return _failure("needs-evidence", workflow)
    refs = [str(item.get("ref", "")) for item in evidence if isinstance(item, dict) and item.get("ref")]
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    disposition = "needs-evidence" if any(item.get("status") == "not_reported" for item in evidence) else "prepared"
    if disposition == "needs-evidence":
        return {
            "status": "PENDING_APPROVAL",
            "workflow": workflow,
            "disposition": disposition,
            "evidence_refs": refs,
            "idempotency_key": f"scm-{digest}",
            "effects": {"sent": False, "applied": False, "mutated_records": False},
            "rollback": ROLLBACK_TARGET,
        }
    if workflow in {"pipeline", "proposal_follow_up", "onboarding", "renewal_risk", "founder_escalation", "other"}:
        status = "PENDING_APPROVAL"
    else:
        status = "COMPLETED"
    return {"status": status, "workflow": workflow, "disposition": disposition, "evidence_refs": refs, "idempotency_key": f"scm-{digest}", "effects": {"sent": False, "applied": False, "mutated_records": False}, "rollback": ROLLBACK_TARGET}


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
