#!/usr/bin/env python3
"""Offline, deterministic helper for synthetic legal-operations preparation."""

import argparse
import hashlib
import json
import re
import sys
from typing import Any

LIVE_MARKERS = re.compile(r"(?:sk_live|api[_-]?key|password|bearer|BEGIN " + r"PRIVATE KEY|customer@example\.com)", re.I)
FORBIDDEN_ACTIONS = {"sign", "accept", "send", "file", "negotiate", "renew", "terminate", "mutate"}


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted preparation summary without legal or external side effects."""
    raw = json.dumps(request, sort_keys=True)
    if LIVE_MARKERS.search(raw) or request.get("privacy_classification") == "restricted":
        return {"status": "FAILED", "disposition": "privacy_rejected", "effects": {"sent": False, "signed": False, "accepted": False, "filed": False, "mutated_records": False}}
    evidence = request.get("source_evidence", [])
    refs = [str(item.get("ref", "")) for item in evidence if isinstance(item, dict) and item.get("ref")]
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    workflow = request.get("workflow", "other")
    missing = not evidence or any(item.get("status") == "not_reported" for item in evidence if isinstance(item, dict))
    disposition = "needs-evidence" if missing else "prepared"
    if request.get("jurisdiction") in (None, "", "unknown", "not_reported") or request.get("workflow") in {"escalation", "playbook_comparison", "other"}:
        status = "PENDING_APPROVAL"
    else:
        status = "COMPLETED"
    requested = set(request.get("requested_actions", [])) if isinstance(request.get("requested_actions"), list) else set()
    if requested & FORBIDDEN_ACTIONS:
        status, disposition = "PENDING_APPROVAL", "authority_escalation"
    return {"status": status, "workflow": workflow, "disposition": disposition, "evidence_refs": refs, "jurisdiction": request.get("jurisdiction", "unknown"), "idempotency_key": f"clo-{digest}", "effects": {"sent": False, "signed": False, "accepted": False, "filed": False, "mutated_records": False}, "rollback": "discard unapproved artifact; restore prior qualified release"}


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
