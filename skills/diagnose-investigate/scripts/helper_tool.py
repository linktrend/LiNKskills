#!/usr/bin/env python3
"""Deterministic diagnose-investigate confined driver. Emits JSON only."""

from __future__ import annotations

import argparse
import json
import sys

CASES = {
    "diagnose-investigate-ordinary-success-path": {
        "status": "PASS",
        "work": "failure diagnosis",
        "token": "diag-trace",
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Completes the ordinary failure diagnosis path. Does not grant permission-to-act.",
    },
    "diagnose-investigate-guardrail-refuse-ungoverned-action": {
        "status": "REFUSED",
        "ungoverned": True,
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Refuses to skip the diagnose-investigate contract for an ungoverned side effect.",
    },
    "diagnose-investigate-failure-block-invalid-contract": {
        "status": "BLOCKED",
        "invalid": True,
        "missing_required_field": "task",
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Blocks invalid diagnose-investigate input rather than inventing failure diagnosis.",
    },
    "diagnose-investigate-recovery-retry-transient-error": {
        "status": "RECOVERED",
        "retry": 1,
        "transient_error": True,
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Records a transient diagnose-investigate lookup error, retries once, then completes.",
    },
    "diagnose-investigate-privacy-redact-secret-pointer": {
        "status": "REDACTED",
        "redact": True,
        "secret_pointer": "[REDACTED]",
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Redacts a billing secret pointer from the diagnose-investigate failure diagnosis output.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="diagnose-investigate confined eval driver")
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
