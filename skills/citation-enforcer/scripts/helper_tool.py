#!/usr/bin/env python3
"""Deterministic citation matrix using LR-WP-002 claim-link relations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "scripts"))

from methodology import (  # noqa: E402
    CLAIM_LINK_RELS,
    claim_graph_errors,
    classify_negative_evidence,
    legacy_router_errors,
    provider_neutrality_errors,
)


def _load(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    return payload


def enforce(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a claim-evidence matrix or a blocking report. Effect-free."""

    claims = payload.get("claims") if isinstance(payload.get("claims"), list) else []
    links = payload.get("claim_links") if isinstance(payload.get("claim_links"), list) else []
    errors = claim_graph_errors(claims, links)
    blob = json.dumps(payload, sort_keys=True)
    errors.extend(provider_neutrality_errors(blob))
    errors.extend(legacy_router_errors(blob))
    citations: list[dict[str, Any]] = []
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append("each claim must be an object")
            continue
        claim_id = str(claim.get("claim_id") or "")
        pointers = claim.get("source_pointers") or []
        rel = str(claim.get("rel") or "cites")
        if rel not in CLAIM_LINK_RELS:
            errors.append(f"claim {claim_id!r} rel is not an accepted citation method")
            rel = "cites"
        negative = classify_negative_evidence({**claim, "rel": rel})
        if negative["finalization"] == "blocked":
            errors.append(f"claim {claim_id!r} {negative['note']}")
        circular = bool(claim.get("circular"))
        if circular:
            errors.append(f"claim {claim_id!r} has circular evidence")
        source_type = str(claim.get("source_type") or "file")
        if source_type not in {"memory", "search", "file"}:
            errors.append(f"claim {claim_id!r} source_type must be memory, search, or file")
        pointer = str(pointers[0]) if isinstance(pointers, list) and pointers else str(claim.get("source_pointer") or "")
        citations.append(
            {
                "claim_id": claim_id,
                "rel": rel,
                "source_type": source_type,
                "source_pointer": pointer,
                "negative_evidence": negative["class"],
                "confidence": claim.get("confidence", "unscored"),
            }
        )
    blocked = bool(errors)
    return {
        "status": "FAILED" if blocked else "SUCCESS",
        "citations": citations,
        "errors": errors,
        "blocked": blocked,
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
        result = enforce(payload)
        if args.mode == "extract" and result["status"] == "SUCCESS":
            result["claim_ids"] = [row["claim_id"] for row in result["citations"]]
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "SUCCESS" else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "errors": [str(exc)], "citations": [], "blocked": True, "external_calls": [], "mutations": []}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
