#!/usr/bin/env python3
"""Offline controller variance summary helper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    """Count review statuses without mutating or persisting input records."""
    observations = payload.get("observations", [])
    if not isinstance(observations, list):
        raise ValueError("observations must be an array")
    status_counts: dict[str, int] = {}
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("each observation must be an object")
        status = observation.get("status", "UNKNOWN")
        if not isinstance(status, str) or not status:
            raise ValueError("observation status must be a non-empty string")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "status": "success",
        "status_counts": dict(sorted(status_counts.items())),
        "external_calls": [],
        "mutations": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize controller observations offline.")
    parser.add_argument("--input", type=Path, help="JSON fixture path; otherwise read JSON from stdin")
    args = parser.parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("input root must be an object")
        print(json.dumps(summarize(payload), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
