#!/usr/bin/env python3
"""Flush extended execution_ledger.jsonl events into lskills.telemetry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from lib.skill_runtime.telemetry import flush_telemetry_buffer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()
    result = flush_telemetry_buffer(repo_root=args.repo_root.resolve(), limit=args.limit)
    print(json.dumps(result, indent=2))
    return 0 if result.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
