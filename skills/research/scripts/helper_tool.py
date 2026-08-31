#!/usr/bin/env python3
"""Validate a redacted research record without external effects."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from methodology import (  # noqa: E402
    evaluate_methodology,
    facade_outcome,
    skill_dependency_cycle_errors,
)


def _load(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    return payload


def _validate_basic(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload.get("claims"), list):
        errors.append("claims must be an array")
    if not isinstance(payload.get("sources"), list):
        errors.append("sources must be an array")
    for claim in payload.get("claims", []):
        if not isinstance(claim, dict) or not claim.get("claim_id") or not claim.get("claim_text"):
            errors.append("each claim needs claim_id and claim_text")
    for source in payload.get("sources", []):
        if not isinstance(source, dict) or not source.get("pointer") or not source.get("source_type"):
            errors.append("each source needs source_type and pointer")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to a redacted JSON record")
    parser.add_argument(
        "--mode",
        choices=("validate", "extract", "methodology", "facade"),
        default="validate",
    )
    args = parser.parse_args()
    try:
        payload = _load(args.input)
        if args.mode == "facade":
            result = {
                **facade_outcome(
                    str(payload.get("requested_skill") or "search-strategy"),
                    new_broad_workflow=bool(payload.get("new_broad_workflow", True)),
                ),
                "status": "SUCCESS",
                "errors": skill_dependency_cycle_errors(
                    {
                        "search-strategy": ["research"],
                        "research": ["citation-enforcer"],
                        "citation-enforcer": [],
                    }
                ),
                "external_calls": [],
                "mutations": [],
            }
            if result["errors"]:
                result["status"] = "FAILED"
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "SUCCESS" else 1
        if args.mode == "methodology":
            result = evaluate_methodology(payload)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "SUCCESS" else 1
        errors = _validate_basic(payload)
        result: dict[str, Any] = {
            "status": "FAILED" if errors else "SUCCESS",
            "errors": errors,
            "claim_count": len(payload.get("claims", [])) if isinstance(payload.get("claims"), list) else 0,
            "source_count": len(payload.get("sources", [])) if isinstance(payload.get("sources"), list) else 0,
            "external_calls": [],
            "mutations": [],
        }
        if args.mode == "extract" and not errors:
            result["claim_ids"] = [str(item["claim_id"]) for item in payload["claims"]]
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1 if errors else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"status": "FAILED", "errors": [str(exc)], "external_calls": [], "mutations": []},
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
