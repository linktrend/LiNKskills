#!/usr/bin/env python3
"""Validate or extract a transport-neutral communication draft.

The helper is deliberately local and deterministic. It never sends, publishes,
calls a service, chooses a transport, or writes outside stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PRIVATE_MARKERS = ("customer_email", "customer_phone", "password", "api_key", "secret")
ALLOWED_AUDIENCES = {"principal", "technical", "agent"}


def load_object(path: Path) -> dict[str, Any]:
    """Read one JSON object from a local file."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def validate(value: dict[str, Any]) -> list[str]:
    """Return stable validation errors for a communication draft."""
    errors: list[str] = []
    audience = value.get("audience")
    if audience not in ALLOWED_AUDIENCES:
        errors.append("audience must be principal, technical, or agent")
    if not isinstance(value.get("message"), str) or not value["message"].strip():
        errors.append("message must be a non-empty string")
    if value.get("status") not in {"DRAFT", "BLOCKED", "READY_FOR_OWNER"}:
        errors.append("status must be DRAFT, BLOCKED, or READY_FOR_OWNER")
    for key in PRIVATE_MARKERS:
        if re.search(rf"\b{re.escape(key)}\b", json.dumps(value, sort_keys=True), re.IGNORECASE):
            errors.append("private or secret marker is not allowed")
            break
    effects = value.get("effects", {})
    if not isinstance(effects, dict):
        errors.append("effects must be an object")
    else:
        for key in ("messages_sent", "external_calls", "mutations"):
            if effects.get(key, []) != []:
                errors.append(f"effects.{key} must be empty")
    if value.get("status") == "READY_FOR_OWNER" and not value.get("evidence"):
        errors.append("READY_FOR_OWNER requires evidence")
    return sorted(set(errors))


def main() -> int:
    """Run the selected deterministic helper mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to one JSON draft")
    parser.add_argument("--mode", choices=("extract", "validate"), default="validate")
    args = parser.parse_args()
    try:
        value = load_object(Path(args.input))
        errors = validate(value)
        output: dict[str, Any] = {
            "status": "FAILED" if errors else "SUCCESS",
            "errors": errors,
            "mode": args.mode,
            "message_length": len(value.get("message", "")) if isinstance(value.get("message"), str) else 0,
            "effects": {"messages_sent": [], "external_calls": [], "mutations": []},
        }
        if args.mode == "extract" and not errors:
            output["audience"] = value["audience"]
            output["message"] = value["message"]
            output["evidence"] = list(value.get("evidence", []))
        print(json.dumps(output, sort_keys=True))
        return 0 if not errors else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "errors": [str(exc)]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
