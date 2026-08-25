#!/usr/bin/env python3
"""Validate supplied operational reporting records without external effects."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

MODES = {"executive_digest", "flash_report", "no_material_change", "supervised_agent_summary", "maintenance_result"}
PRIVATE_MARKERS = ("customer_email", "customer_phone", "password", "api_key", "secret", "selfie")


def validate(payload: dict[str, Any]) -> list[str]:
    """Return stable validation errors for supplied report inputs."""
    errors: list[str] = []
    if payload.get("mode") not in MODES:
        errors.append("mode is not supported")
    if payload.get("window") not in {"morning", "evening", "custom"}:
        errors.append("window must be morning, evening, or custom")
    if not isinstance(payload.get("records"), list):
        errors.append("records must be an array")
    else:
        for index, record in enumerate(payload["records"]):
            if not isinstance(record, dict):
                errors.append(f"records[{index}] must be an object")
                continue
            if record.get("status") == "verified_completed" and not record.get("evidence_pointer"):
                errors.append(f"records[{index}] verified_completed requires evidence_pointer")
            if record.get("kind") == "mail" and record.get("is_own_mailbox") is not True:
                errors.append(f"records[{index}] mail must be explicitly own mailbox")
            if record.get("is_routine") is True:
                errors.append(f"records[{index}] Routine records must be omitted")
    encoded = json.dumps(payload, sort_keys=True)
    if any(re.search(rf"\b{re.escape(marker)}\b", encoded, re.IGNORECASE) for marker in PRIVATE_MARKERS):
        errors.append("private, health, or selfie marker is not allowed")
    return sorted(set(errors))


def main() -> int:
    """Run validation or deterministic one-line rendering."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--mode", choices=("validate", "render-no-change"), default="validate")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        errors = validate(payload)
        result: dict[str, Any] = {"status": "FAILED" if errors else "SUCCESS", "errors": errors, "effects": {"messages_sent": [], "external_calls": [], "mutations": []}}
        if args.mode == "render-no-change" and not errors:
            if payload.get("mode") != "no_material_change":
                result = {"status": "FAILED", "errors": ["render-no-change requires no_material_change mode"], "effects": {"messages_sent": [], "external_calls": [], "mutations": []}}
            else:
                result["message"] = "No material verified change in the supplied window."
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "SUCCESS" else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "errors": [str(exc)]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
