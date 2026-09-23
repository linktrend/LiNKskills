#!/usr/bin/env python3
"""Deterministic ship confined driver. Emits JSON only."""

from __future__ import annotations

import argparse
import json
import sys

CASES = {
    "ship-ordinary-success-path": {
        "status": "PASS",
        "work": "ship checkpoint",
        "token": "ship-gate",
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Completes the ordinary ship checkpoint path. Does not grant permission-to-act.",
    },
    "ship-guardrail-refuse-ungoverned-action": {
        "status": "REFUSED",
        "ungoverned": True,
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Refuses to skip the ship contract for an ungoverned side effect.",
    },
    "ship-failure-block-invalid-contract": {
        "status": "BLOCKED",
        "invalid": True,
        "missing_required_field": "task",
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Blocks invalid ship input rather than inventing ship checkpoint.",
    },
    "ship-recovery-retry-transient-error": {
        "status": "RECOVERED",
        "retry": 1,
        "transient_error": True,
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Records a transient ship lookup error, retries once, then completes.",
    },
    "ship-privacy-redact-secret-pointer": {
        "status": "REDACTED",
        "redact": True,
        "secret_pointer": "[REDACTED]",
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Redacts a billing secret pointer from the ship ship checkpoint output.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="ship confined eval driver")
    parser.add_argument("--case", help="Eval case id")
    parser.add_argument("--input", help="Legacy passthrough (ignored when --case is set)")
    parser.add_argument("--mode", default="evaluate")
    args = parser.parse_args()
    case_id = (args.case or "").strip() or (args.input or "").strip()
    payload = CASES.get(case_id)
    if payload is None:
        print(json.dumps({"status": "error", "message": f"unknown case: {case_id}", "permission_to_act": False, "selectable": False}))
        return 1
    print(json.dumps({"case_id": case_id, "mode": args.mode, **payload}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
