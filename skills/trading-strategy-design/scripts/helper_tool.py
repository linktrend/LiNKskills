#!/usr/bin/env python3
"""Validate a supplied skill input/output object against its local static schema.

This developer/auditor helper reports structural validity only. It does not
score method quality, produce a behavioral PASS, fetch data, or write artifacts.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser(description="Check supplied JSON object shape only")
    parser.add_argument("--kind", choices=["input", "output"], required=True)
    parser.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    repo_root = skill_root.parents[1]
    sys.path.insert(0, str(repo_root / "packages" / "contracts"))
    try:
        from linkskills_contracts.validate import validate_instance
        schema_doc = json.loads((skill_root / "references" / "schemas.json").read_text())
        instance = json.loads(args.file.read_text())
        result = validate_instance(instance, schema_doc["definitions"][args.kind])
    except Exception as exc:
        print(json.dumps({"status": "STRUCTURE_CHECK_ERROR", "error": str(exc)}, indent=2))
        return 2
    if result.ok:
        print(json.dumps({"status": "STRUCTURE_VALID", "kind": args.kind, "method_qualified": False}, indent=2))
        return 0
    print(json.dumps({"status": "STRUCTURE_INVALID", "kind": args.kind, "errors": [str(e) for e in result.errors], "method_qualified": False}, indent=2))
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
