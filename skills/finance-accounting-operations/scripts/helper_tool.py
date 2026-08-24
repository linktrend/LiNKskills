#!/usr/bin/env python3
"""Deterministic read-only summaries for finance operations fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


def _amount(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"amount must be numeric: {value!r}") from exc


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    """Return totals without mutating or persisting the input records."""
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("records must be an array")
    totals: dict[str, Decimal] = {}
    counts: dict[str, int] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each record must be an object")
        kind = record.get("kind")
        if not isinstance(kind, str) or not kind:
            raise ValueError("each record requires a kind")
        totals[kind] = totals.get(kind, Decimal("0")) + _amount(record.get("amount", 0))
        counts[kind] = counts.get(kind, 0) + 1
    return {
        "status": "success",
        "totals": {key: str(value) for key, value in sorted(totals.items())},
        "counts": dict(sorted(counts.items())),
        "external_calls": [],
        "mutations": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize supplied finance records; never calls Odoo.")
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
