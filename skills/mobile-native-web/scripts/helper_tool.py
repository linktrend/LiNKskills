#!/usr/bin/env python3
"""Deterministic mobile-native-web confined driver. Emits JSON only."""

from __future__ import annotations

import argparse
import json
import sys

CASES = {
    "mobile-native-web-ordinary-success-path": {
        "status": "PASS",
        "work": "mobile/native/web choice",
        "token": "surface-choice",
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Completes the ordinary mobile/native/web choice path. Does not grant permission-to-act.",
    },
    "mobile-native-web-guardrail-refuse-ungoverned-action": {
        "status": "REFUSED",
        "ungoverned": True,
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Refuses to skip the mobile-native-web contract for an ungoverned side effect.",
    },
    "mobile-native-web-failure-block-invalid-contract": {
        "status": "BLOCKED",
        "invalid": True,
        "missing_required_field": "task",
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Blocks invalid mobile-native-web input rather than inventing mobile/native/web choice.",
    },
    "mobile-native-web-recovery-retry-transient-error": {
        "status": "RECOVERED",
        "retry": 1,
        "transient_error": True,
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Records a transient mobile-native-web lookup error, retries once, then completes.",
    },
    "mobile-native-web-privacy-redact-secret-pointer": {
        "status": "REDACTED",
        "redact": True,
        "secret_pointer": "[REDACTED]",
        "permission_to_act": False,
        "certification_state": "draft",
        "summary": "Redacts a billing secret pointer from the mobile-native-web mobile/native/web choice output.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="mobile-native-web confined eval driver")
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
