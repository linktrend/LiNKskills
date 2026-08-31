#!/usr/bin/env python3
"""One-way search-strategy facade. Does not execute retrieval or a legacy router."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "scripts"))

from methodology import (  # noqa: E402
    facade_outcome,
    legacy_router_errors,
    provider_neutrality_errors,
    skill_dependency_cycle_errors,
)


FAMILY_GRAPH = {
    "search-strategy": ["research"],
    "research": ["citation-enforcer"],
    "citation-enforcer": [],
}


def _load(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    return payload


def route(payload: dict[str, Any]) -> dict[str, Any]:
    """Map a search-strategy invocation onto canonical research. Effect-free."""

    blob = json.dumps(payload, sort_keys=True)
    errors = provider_neutrality_errors(blob) + legacy_router_errors(blob)
    errors.extend(skill_dependency_cycle_errors(FAMILY_GRAPH))
    requested = str(payload.get("requested_skill") or "search-strategy")
    outcome = facade_outcome(
        requested,
        new_broad_workflow=bool(payload.get("new_broad_workflow", True)),
    )
    if payload.get("use_legacy_router"):
        errors.append("legacy research router is excluded")
    status = "FAILED" if errors else "SUCCESS"
    return {
        **outcome,
        "status": status,
        "errors": errors,
        "tier_used": "none",
        "confidence": 0,
        "findings": [],
        "external_calls": [],
        "mutations": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--mode", choices=("validate", "extract", "transform"), default="validate")
    args = parser.parse_args()
    try:
        payload = _load(args.input)
        result = route(payload)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "SUCCESS" else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "errors": [str(exc)], "external_calls": [], "mutations": []}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
