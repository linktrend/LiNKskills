#!/usr/bin/env python3
"""Offline, deterministic helper for synthetic sales-management preparation."""

import argparse
import hashlib
import json
import re
import sys
from typing import Any

LIVE_MARKERS = re.compile(r"(?:sk_live|api[_-]?key|password|bearer|\+?\d[\d ()-]{7,})", re.I)


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted, owner-bound preparation summary without external effects."""
    raw = json.dumps(request, sort_keys=True)
    if LIVE_MARKERS.search(raw) or request.get("privacy_classification") == "restricted":
        return {"status": "FAILED", "disposition": "privacy_rejected", "effects": {"sent": False, "applied": False, "mutated_records": False}}
    evidence = request.get("source_evidence", [])
    refs = [str(item.get("ref", "")) for item in evidence if isinstance(item, dict) and item.get("ref")]
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    workflow = request.get("workflow", "other")
    disposition = "needs-evidence" if not evidence or any(item.get("status") == "not_reported" for item in evidence if isinstance(item, dict)) else "prepared"
    if workflow in {"pipeline", "proposal_follow_up", "onboarding", "renewal_risk", "founder_escalation", "other"}:
        status = "PENDING_APPROVAL"
    else:
        status = "COMPLETED"
    return {"status": status, "workflow": workflow, "disposition": disposition, "evidence_refs": refs, "idempotency_key": f"scm-{digest}", "effects": {"sent": False, "applied": False, "mutated_records": False}, "rollback": "discard unapproved draft; restore prior qualified release"}


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
