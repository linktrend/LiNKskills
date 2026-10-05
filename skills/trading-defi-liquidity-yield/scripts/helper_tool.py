#!/usr/bin/env python3
"""Read-only JSON syntax check for explicitly named package artifacts; no network or mutations."""
import argparse, json
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="package-relative JSON artifact paths")
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    for raw in args.paths:
        candidate=(root/raw).resolve()
        if root.resolve() not in candidate.parents or candidate.suffix != ".json":
            parser.error(f"path must be a package-local .json file: {raw}")
        try:
            json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"INVALID {raw}: {exc}")
            return 1
        print(f"JSON_SYNTAX_OK {raw}; schema and behavior not evaluated")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
