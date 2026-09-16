#!/usr/bin/env python3
"""Confined remainder eval driver. Effect-free JSON only; never certifies usable."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CASES_REL = Path("references") / "remainder-eval-cases.json"


def _load_cases(skill_dir: Path) -> dict:
    path = skill_dir / CASES_REL
    if not path.is_file():
        raise FileNotFoundError(path.as_posix())
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), dict):
        raise ValueError("remainder-eval-cases.json must contain a cases object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--mode", default="evaluate")
    args = parser.parse_args()
    skill_dir = Path(__file__).resolve().parents[1]
    payload = _load_cases(skill_dir)
    case_id = str(args.case).strip()
    case = payload["cases"].get(case_id)
    if not isinstance(case, dict):
        print(
            json.dumps(
                {
                    "status": "error",
                    "case_id": case_id,
                    "message": f"unknown case: {case_id}",
                    "permission_to_act": False,
                    "certification_state": "draft",
                    "selectable": False,
                    "external_calls": [],
                    "mutations": [],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    result = {
        "case_id": case_id,
        "mode": args.mode,
        "skill_id": payload.get("skill_id"),
        "permission_to_act": False,
        "certification_state": "draft",
        "selectable": False,
        "usable_claimed": False,
        "external_calls": [],
        "mutations": [],
        **case,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
