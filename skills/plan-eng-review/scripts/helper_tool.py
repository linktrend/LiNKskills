#!/usr/bin/env python3
"""Deterministic local input check. Never routes to another skill."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    try:
        value = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "errors": [str(exc)]}))
        return 1
    errors = []
    if not isinstance(value, dict) or not str(value.get("task") or "").strip():
        errors.append("task is required")
    blob = json.dumps(value).lower()
    for marker in ("api_key", "password", "secret_key", "private_key"):
        if marker in blob:
            errors.append("secret marker is not allowed")
            break
    out = {
        "status": "FAILED" if errors else "SUCCESS",
        "errors": errors,
        "effects": {"external_calls": [], "mutations": []},
    }
    print(json.dumps(out, sort_keys=True))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
