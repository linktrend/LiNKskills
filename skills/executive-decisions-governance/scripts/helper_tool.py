#!/usr/bin/env python3
"""Deterministic, side-effect-free executive decision brief helper."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROLLBACK = "ABSENT@517f22ee135c298a17a74f84a84b60accdf22cf4/tree:d2514ee298074c70f9bb5fb19f2fc71af7d43f16"
MODES = {"decision_brief", "record_decision", "rule_impact", "implementation_tracking"}
BLOCKED_ACTIONS = {"approve", "activate", "enforce", "send", "schedule", "create_task", "unknown"}
PRIVATE_MARKERS = ("customer@example.com", "password", "api_key", "access_token", "private key", "begin private key", "social security", "phone number")


def _effects() -> dict[str, list[Any]]:
    """Return the immutable empty-effects contract."""
    return {"messages_sent": [], "external_calls": [], "mutations": []}


def _base(request: dict[str, Any], status: str, refs: list[str], uncertainty: list[str] | None = None) -> dict[str, Any]:
    """Create the strict output envelope without echoing raw input."""
    mode = str(request.get("mode") or "unknown")
    matter_ref = str(request.get("matter_ref") or "matter:unknown")
    matter = str(request.get("matter") or "Matter not reported")
    return {
        "status": status,
        "mode": mode,
        "matter_ref": matter_ref,
        "brief": {"matter": matter, "risks": list(request.get("risks") or []), "recommendation": str(request.get("recommendation") or "Recommendation not reported")},
        "choices": list(request.get("choices") or []),
        "decision": request.get("decision_record") or {"status": "not_reported"},
        "rule_impact": request.get("rule_impact") or {"status": "not_reported", "summary": "Rule impact not reported"},
        "implementation_tracking": list(request.get("implementation_tracking") or []),
        "evidence": refs or ["fixture:missing"],
        "uncertainty": list(uncertainty or []),
        "authority": {"owner_ref": "not_reported", "approval_recorded": False, "activated": False},
        "effects": _effects(),
        "rollback": ROLLBACK,
    }


def _failure(request: dict[str, Any], reason: str, refs: list[str] | None = None) -> dict[str, Any]:
    """Return a safe blocked result with a typed reason only."""
    return _base(request, "BLOCKED", refs or [], [reason])


def _refs(raw: Any) -> tuple[list[str], str | None]:
    """Validate evidence references and statuses."""
    if not isinstance(raw, list) or not raw:
        return [], "source_evidence must contain at least one reference"
    refs: list[str] = []
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
            return [], "each source evidence item requires a reference"
        ref = item["ref"]
        if not re.fullmatch(r"(?:fixture|source|consumer):[^\s]+", ref):
            return [], "source references must use fixture, source, or consumer namespaces"
        if item.get("status") not in {"confirmed", "reported", "not_reported"}:
            return [], "each source evidence item requires an explicit status"
        if ref in refs:
            return [], "duplicate evidence references are rejected"
        refs.append(ref)
    return refs, None


def _private(value: Any) -> bool:
    """Detect obvious private or credential markers without retaining content."""
    blob = json.dumps(value, sort_keys=True, ensure_ascii=False).lower()
    return any(marker in blob for marker in PRIVATE_MARKERS)


def _choice_error(choices: Any) -> str | None:
    """Validate choice identity, tradeoffs, and the explicit escape hatch."""
    if not isinstance(choices, list) or len(choices) < 2:
        return "at least two choices with tradeoffs are required"
    ids: set[str] = set()
    has_other = False
    for item in choices:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) and item[key].strip() for key in ("id", "label", "tradeoff")):
            return "each choice requires id, label, and tradeoff"
        if item["id"] in ids:
            return "duplicate choice ids are rejected"
        ids.add(item["id"])
        has_other = has_other or item["label"] == "Other — specify"
    if not has_other:
        return "non-exhaustive choices require the exact Other — specify escape hatch"
    return None


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Normalize one request into a deterministic, side-effect-free artifact."""
    if not isinstance(request, dict):
        return _failure({}, "request must be an object")
    if request.get("mode") not in MODES:
        return _failure(request, "unknown mode is rejected")
    if request.get("privacy_classification") not in {"synthetic", "redacted", "public"}:
        return _failure(request, "privacy classification must be synthetic, redacted, or public")
    refs, error = _refs(request.get("source_evidence"))
    if error:
        return _failure(request, error, refs)
    if not isinstance(request.get("matter_ref"), str) or not re.fullmatch(r"matter:[A-Za-z0-9][A-Za-z0-9._:-]{2,127}", request["matter_ref"]):
        return _failure(request, "a unique matter_ref is required", refs)
    if not isinstance(request.get("matter"), str) or len(request["matter"].strip()) < 3:
        return _failure(request, "matter must be stated before background", refs)
    if _private(request):
        return _failure(request, "private identifiers, credentials, or confidential records are not accepted", refs)
    if request.get("requested_action") in BLOCKED_ACTIONS:
        return _failure(request, "the requested action exceeds the skill authority boundary", refs)
    if request.get("mode") == "decision_brief":
        choice_error = _choice_error(request.get("choices"))
        if choice_error:
            return _failure(request, choice_error, refs)
        if not isinstance(request.get("recommendation"), str) or not request["recommendation"].strip():
            return _failure(request, "decision briefs require a separate recommendation", refs)
    decision = request.get("decision_record")
    if decision is not None:
        if not isinstance(decision, dict) or decision.get("status") not in {"proposed", "approved", "rejected", "not_reported"}:
            return _failure(request, "decision_record status is invalid", refs)
        if decision.get("status") == "approved":
            if not isinstance(decision.get("choice_id"), str) or not isinstance(decision.get("owner_ref"), str):
                return _failure(request, "an approved record requires choice_id and owner_ref", refs)
            choice_ids = {item.get("id") for item in request.get("choices", []) if isinstance(item, dict)}
            if decision["choice_id"] not in choice_ids:
                return _failure(request, "approved choice_id must match a supplied choice", refs)
    if request.get("mode") == "rule_impact" and not isinstance(request.get("rule_impact"), dict):
        return _failure(request, "rule_impact mode requires a descriptive rule impact record", refs)
    tracking = request.get("implementation_tracking") or []
    if not isinstance(tracking, list):
        return _failure(request, "implementation_tracking must be a list", refs)
    tracking_ids: set[str] = set()
    for item in tracking:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) and item[key].strip() for key in ("id", "item", "owner_ref", "status", "evidence_ref")):
            return _failure(request, "tracking items require id, item, owner_ref, status, and evidence_ref", refs)
        if item["id"] in tracking_ids:
            return _failure(request, "duplicate implementation tracking ids are rejected", refs)
        tracking_ids.add(item["id"])
        if item["evidence_ref"] not in refs:
            return _failure(request, "tracking evidence_ref must match supplied evidence", refs)
    result = _base(request, "READY_FOR_OWNER", refs)
    result["uncertainty"] = [item["ref"] + " is not_reported" for item in request["source_evidence"] if item.get("status") == "not_reported"]
    if result["uncertainty"]:
        result["status"] = "DRAFT"
    if isinstance(decision, dict) and decision.get("status") == "approved":
        result["authority"] = {"owner_ref": decision["owner_ref"], "approval_recorded": False, "activated": False}
        result["uncertainty"].append("supplied approval is recorded as owner evidence only; no activation occurred")
    return result


def main() -> int:
    """Run the helper against stdin or a JSON file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON request path; otherwise read stdin")
    args = parser.parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        result = normalize_request(json.loads(raw))
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] != "BLOCKED" else 1
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps(_failure({}, str(exc), ["fixture:parse"]), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
