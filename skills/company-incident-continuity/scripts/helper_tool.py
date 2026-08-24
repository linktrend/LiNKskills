#!/usr/bin/env python3
"""Deterministic, side-effect-free incident and continuity review helper."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


MODES = {"incident_intake", "outage_review", "security_coordination", "continuity_review", "recovery_decision", "closure_review"}
INCIDENT_TYPES = {"outage", "security", "continuity", "data_integrity", "other"}
STATES = {"detected", "triaged", "mitigating", "recovering", "monitoring", "closed", "unknown"}
SEVERITIES = {"low", "medium", "high", "critical", "unknown"}
IMPACT_STATES = {"observed", "suspected", "unknown"}
OPTION_STATES = {"proposed", "supplied", "not_reported"}
COMMUNICATION_STATES = {"draft", "supplied", "unsent", "not_reported"}
BLOCKED_ACTIONS = {"deploy", "rollback", "isolate", "rotate_credentials", "send", "approve", "close", "schedule", "mutate_program", "unknown"}
PRIVATE_MARKERS = ("customer@example.com", "password", "api_key", "access_token", "private key", "begin private key", "credential", "confidential", "restricted incident")
ROLLBACK = "ABSENT@cb5a7d469a64b49b141893359ff72cb65fba998c/tree:8e92f50bdfda1ac61035fa10444b519d5f2aebb2"


def _effects() -> dict[str, list[Any]]:
    """Return the immutable empty-effects contract."""
    return {"messages_sent": [], "external_calls": [], "mutations": []}


def _base(request: dict[str, Any], status: str, refs: list[str], uncertainty: list[str] | None = None) -> dict[str, Any]:
    """Create a safe result envelope without echoing raw request content."""
    incident_ref = request.get("incident_ref") if isinstance(request.get("incident_ref"), str) else "incident:unknown"
    incident_type = request.get("incident_type") if request.get("incident_type") in INCIDENT_TYPES else "not_reported"
    severity = request.get("severity") if request.get("severity") in SEVERITIES else "unknown"
    state = request.get("state") if request.get("state") in STATES else "unknown"
    return {
        "status": status, "mode": str(request.get("mode") or "unknown"), "incident_ref": incident_ref,
        "incident_type": incident_type, "severity": severity, "state": state,
        "owner": {"responder_ref": "not_reported", "platform_ref": "not_reported", "program_ledger_ref": "not_reported", "deployment_authority_ref": "not_reported"},
        "impacts": [], "recovery_options": [], "communications": [], "closure": {"status": "not_reported", "activated": False},
        "evidence": refs or ["fixture:missing"], "uncertainty": list(uncertainty or []),
        "ownership": {"incident_mutated": False, "program_ledger_mutated": False, "deployment_mutated": False},
        "effects": _effects(), "rollback": ROLLBACK,
    }


def _failure(request: dict[str, Any], reason: str, refs: list[str] | None = None) -> dict[str, Any]:
    """Return a typed blocked result without sensitive input."""
    return _base(request, "BLOCKED", refs or [], [reason])


def _private(value: Any) -> bool:
    """Detect private or credential markers without retaining their values."""
    blob = json.dumps(value, sort_keys=True, ensure_ascii=False).lower()
    return any(marker in blob for marker in PRIVATE_MARKERS)


def _refs(raw: Any) -> tuple[list[str], str | None, set[str]]:
    """Validate evidence references and statuses."""
    if not isinstance(raw, list) or not raw:
        return [], "source_evidence must contain at least one reference", set()
    refs: list[str] = []
    unknown: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
            return [], "each source evidence item requires a reference", set()
        ref = item["ref"]
        if not re.fullmatch(r"(?:fixture|source|consumer):[^\s]+", ref):
            return [], "evidence references require fixture, source, or consumer namespaces", set()
        if item.get("status") not in {"confirmed", "reported", "not_reported"}:
            return [], "each evidence item requires an explicit status", set()
        if ref in refs:
            return [], "duplicate evidence references are rejected", set()
        refs.append(ref)
        if item["status"] == "not_reported":
            unknown.add(ref)
    return refs, None, unknown


def _impacts(raw: Any, refs: set[str]) -> tuple[list[dict[str, Any]], str | None]:
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return [], "impacts must be an array"
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) for key in ("id", "scope", "status", "evidence_ref")):
            return [], "each impact requires id, scope, status, and evidence_ref"
        if not re.fullmatch(r"impact:[A-Za-z0-9][A-Za-z0-9._:-]{2,63}", item["id"]) or item["id"] in ids or item["status"] not in IMPACT_STATES or item["evidence_ref"] not in refs:
            return [], "impacts require unique references, supported states, and supplied evidence"
        rows.append({"id": item["id"], "scope": item["scope"], "status": item["status"], "note": item.get("note", "not_reported"), "evidence_ref": item["evidence_ref"]})
        ids.add(item["id"])
    return rows, None


def _options(raw: Any, refs: set[str]) -> tuple[list[dict[str, Any]], str | None]:
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return [], "recovery_options must be an array"
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    has_other = False
    for item in raw:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) for key in ("id", "label", "tradeoff", "evidence_ref")):
            return [], "each recovery option requires id, label, tradeoff, and evidence_ref"
        if item["id"] in ids or item.get("status", "proposed") not in OPTION_STATES:
            return [], "recovery options require unique ids and supported status"
        if item["evidence_ref"] not in refs:
            return [], "recovery option evidence_ref must match supplied evidence"
        has_other = has_other or item["label"] == "Other — specify"
        rows.append({"id": item["id"], "label": item["label"], "tradeoff": item["tradeoff"], "status": item.get("status", "proposed"), "evidence_ref": item["evidence_ref"]})
        ids.add(item["id"])
    if len(rows) > 1 and not has_other:
        return [], "non-exhaustive recovery choices require the exact Other — specify escape hatch"
    return rows, None


def _communications(raw: Any, refs: set[str]) -> tuple[list[dict[str, Any]], str | None]:
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return [], "communications must be an array"
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) for key in ("id", "audience", "status", "evidence_ref")):
            return [], "each communication requires id, audience, status, and evidence_ref"
        if item["id"] in ids or item["status"] not in COMMUNICATION_STATES or item["evidence_ref"] not in refs:
            return [], "communications require unique ids, supported states, and supplied evidence"
        rows.append({"id": item["id"], "audience": item["audience"], "status": item["status"], "summary": item.get("summary", "not_reported"), "evidence_ref": item["evidence_ref"], "sent": False})
        ids.add(item["id"])
    return rows, None


def _closure(raw: Any, refs: set[str]) -> tuple[dict[str, Any], str | None]:
    if raw is None:
        return {"status": "not_reported", "activated": False}, None
    if not isinstance(raw, dict) or raw.get("status") not in {"proposed", "supplied"}:
        return {"status": "not_reported", "activated": False}, "closure status must be proposed or supplied"
    evidence_refs = raw.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs or any(ref not in refs for ref in evidence_refs):
        return {"status": "not_reported", "activated": False}, "closure requires supplied evidence_refs"
    if not isinstance(raw.get("residual_risks", []), list):
        return {"status": "not_reported", "activated": False}, "closure residual_risks must be an array"
    return {"status": raw["status"].upper(), "evidence_refs": evidence_refs, "residual_risks": raw.get("residual_risks", []), "owner_ref": raw.get("owner_ref", "not_reported"), "activated": False}, None


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Normalize one incident request into a deterministic review artifact."""
    if not isinstance(request, dict):
        return _failure({}, "request must be an object")
    if request.get("mode") not in MODES:
        return _failure(request, "unknown incident mode is rejected")
    if request.get("privacy_classification") not in {"synthetic", "redacted", "public"}:
        return _failure(request, "privacy classification must be synthetic, redacted, or public")
    refs, error, unknown = _refs(request.get("source_evidence"))
    if error:
        return _failure(request, error, refs)
    if _private(request):
        return _failure(request, "private identifiers, credentials, or confidential incident data are not accepted", refs)
    if request.get("requested_action") in BLOCKED_ACTIONS:
        return _failure(request, "requested action exceeds incident and continuity authority", refs)
    if not isinstance(request.get("incident_ref"), str) or not re.fullmatch(r"incident:[A-Za-z0-9][A-Za-z0-9._:-]{2,127}", request["incident_ref"]):
        return _failure(request, "a unique incident_ref is required", refs)
    if request.get("incident_type") not in INCIDENT_TYPES or request.get("severity") not in SEVERITIES or request.get("state") not in STATES:
        return _failure(request, "incident type, severity, and observed state are required", refs)
    owner = request.get("owner")
    if not isinstance(owner, dict) or not all(isinstance(owner.get(key), str) and owner[key].strip() for key in ("responder_ref", "platform_ref", "program_ledger_ref", "deployment_authority_ref")):
        return _failure(request, "responder, Platform, Program Ledger, and deployment authority ownership are required", refs)
    impacts, error = _impacts(request.get("impacts"), set(refs))
    if error:
        return _failure(request, error, refs)
    options, error = _options(request.get("recovery_options"), set(refs))
    if error:
        return _failure(request, error, refs)
    communications, error = _communications(request.get("communications"), set(refs))
    if error:
        return _failure(request, error, refs)
    closure, error = _closure(request.get("closure"), set(refs))
    if error:
        return _failure(request, error, refs)
    uncertainty = [f"{ref} is not_reported" for ref in sorted(unknown)]
    if request.get("state") == "closed" and closure["status"] == "not_reported":
        uncertainty.append("closure evidence is not_reported")
    result = _base(request, "DRAFT" if uncertainty else "READY_FOR_OWNER", refs, uncertainty)
    result.update({"owner": owner, "impacts": impacts, "recovery_options": options, "communications": communications, "closure": closure})
    return result


def main() -> int:
    """Run the helper against stdin or a JSON file."""
    parser = argparse.ArgumentParser(description="Review supplied incident evidence without external effects or state mutation.")
    parser.add_argument("--input", type=Path, help="JSON request path; otherwise read JSON from stdin")
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
