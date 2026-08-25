#!/usr/bin/env python3
"""Deterministic, side-effect-free planning and performance review helper."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


HORIZONS = {"monthly", "rolling_4_week", "quarterly", "annual", "three_year", "five_year"}
MODES = {"plan_review", "kpi_review", "variance_review", "reprioritization"}
BLOCKED_ACTIONS = {"approve", "activate", "enforce", "send", "schedule", "create_task", "mutate_program", "unknown"}
SIGNAL_STATES = {"on_track", "late", "blocked", "obsolete"}
PRIVATE_MARKERS = (
    "customer@example.com", "password", "api_key", "access_token", "private key",
    "begin private key", "social security", "phone number", "confidential",
)
ROLLBACK = "ABSENT@b619b3317db640d794b528ecc2afbff465f4aea9/tree:4cfcecaafa88b1fedf9096b17e305a93b8b60850"


def _effects() -> dict[str, list[Any]]:
    """Return the immutable empty-effects contract."""
    return {"messages_sent": [], "external_calls": [], "mutations": []}


def _base(request: dict[str, Any], status: str, refs: list[str], uncertainty: list[str] | None = None) -> dict[str, Any]:
    """Create a safe output envelope without echoing untrusted input."""
    plan_ref = request.get("plan_ref") if isinstance(request.get("plan_ref"), str) else "plan:unknown"
    horizon = request.get("horizon") if request.get("horizon") in HORIZONS else "not_reported"
    period = request.get("period") if isinstance(request.get("period"), str) else "not_reported"
    return {
        "status": status,
        "mode": str(request.get("mode") or "unknown"),
        "plan_ref": plan_ref,
        "horizon": horizon,
        "period": period,
        "objectives": [],
        "kpis": [],
        "signals": [],
        "reprioritization": {"status": "not_reported"},
        "evidence": refs or ["fixture:missing"],
        "uncertainty": list(uncertainty or []),
        "ownership": {"mutable_state_created": False, "duplicate_state_created": False},
        "effects": _effects(),
        "rollback": ROLLBACK,
    }


def _failure(request: dict[str, Any], reason: str, refs: list[str] | None = None) -> dict[str, Any]:
    """Return a safe blocked result with a typed reason only."""
    return _base(request, "BLOCKED", refs or [], [reason])


def _private(value: Any) -> bool:
    """Detect obvious private or credential markers without retaining content."""
    blob = json.dumps(value, sort_keys=True, ensure_ascii=False).lower()
    return any(marker in blob for marker in PRIVATE_MARKERS)


def _refs(raw: Any) -> tuple[list[str], str | None, set[str]]:
    """Validate evidence references and return their statuses."""
    if not isinstance(raw, list) or not raw:
        return [], "source_evidence must contain at least one reference", set()
    refs: list[str] = []
    statuses: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
            return [], "each source evidence item requires a reference", set()
        ref = item["ref"]
        if not re.fullmatch(r"(?:fixture|source|consumer):[^\s]+", ref):
            return [], "source references must use fixture, source, or consumer namespaces", set()
        if item.get("status") not in {"confirmed", "reported", "not_reported"}:
            return [], "each source evidence item requires an explicit status", set()
        if ref in refs:
            return [], "duplicate evidence references are rejected", set()
        refs.append(ref)
        statuses.add(item["status"])
    return refs, None, statuses


def _decimal(value: Any) -> Decimal | None:
    """Parse finite numeric evidence without accepting booleans."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return number if number.is_finite() else None


def _precision_ok(value: Any, precision: Any) -> bool:
    """Reject numeric claims that exceed their declared precision."""
    if value is None:
        return True
    if precision == "directional":
        return False
    number = _decimal(value)
    if number is None or precision not in {"whole", "one_decimal", "two_decimal", "three_decimal"}:
        return False
    allowed = {"whole": 0, "one_decimal": 1, "two_decimal": 2, "three_decimal": 3}[precision]
    return max(0, -number.as_tuple().exponent) <= allowed


def _objective_rows(raw: Any, refs: set[str]) -> tuple[list[dict[str, Any]], str | None]:
    if not isinstance(raw, list) or not raw:
        return [], "at least one evidence-linked objective is required"
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            return [], "each objective must be an object"
        oid, statement, evidence_ref = item.get("id"), item.get("statement"), item.get("evidence_ref")
        if not all(isinstance(value, str) and value.strip() for value in (oid, statement, evidence_ref)):
            return [], "each objective requires id, statement, and evidence_ref"
        if not re.fullmatch(r"objective:[A-Za-z0-9][A-Za-z0-9._:-]{2,63}", oid) or oid in ids:
            return [], "objective ids must be unique objective references"
        if evidence_ref not in refs:
            return [], "objective evidence_ref must match supplied evidence"
        ids.add(oid)
        rows.append({"id": oid, "statement": statement, "owner_ref": item.get("owner_ref", "not_reported"), "evidence_ref": evidence_ref})
    return rows, None


def _kpi_rows(raw: Any, refs: set[str], period: str, uncertainty: list[str]) -> tuple[list[dict[str, Any]], str | None]:
    if not isinstance(raw, list):
        return [], "kpis must be an array"
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            return [], "each KPI must be an object"
        kid, name, unit, evidence_ref = (item.get(key) for key in ("id", "name", "unit", "evidence_ref"))
        if not all(isinstance(value, str) and value.strip() for value in (kid, name, unit, evidence_ref)):
            return [], "each KPI requires id, name, unit, and evidence_ref"
        if not re.fullmatch(r"kpi:[A-Za-z0-9][A-Za-z0-9._:-]{2,63}", kid) or kid in ids:
            return [], "KPI ids must be unique KPI references"
        if evidence_ref not in refs:
            return [], "KPI evidence_ref must match supplied evidence"
        kpi_period = item.get("period", period)
        if kpi_period != period:
            return [], "KPI period must match the requested planning period"
        precision = item.get("precision", "whole")
        values = {key: item.get(key) for key in ("target", "forecast", "actual")}
        if any(not _precision_ok(value, precision) for value in values.values()):
            return [], "numeric KPI values require honest declared precision"
        target, forecast, actual = (_decimal(values[key]) for key in ("target", "forecast", "actual"))
        variance: str | None = None
        variance_status = "NOT_COMPARABLE"
        if forecast is not None and actual is not None and item.get("unit") and kpi_period == period:
            variance = str(actual - forecast)
            variance_status = "COMPARABLE"
        else:
            uncertainty.append(f"{kid} forecast-versus-actual variance is not_comparable")
        rows.append({
            "id": kid, "name": name, "unit": unit, "period": kpi_period,
            "target": values["target"], "forecast": values["forecast"], "actual": values["actual"],
            "variance": variance, "variance_status": variance_status, "precision": precision,
            "evidence_ref": evidence_ref,
        })
        ids.add(kid)
    return rows, None


def _signal_rows(raw: Any, refs: set[str]) -> tuple[list[dict[str, Any]], str | None]:
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return [], "signals must be an array"
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) for key in ("id", "status", "evidence_ref")):
            return [], "each signal requires id, status, and evidence_ref"
        if item["id"] in ids or item["status"] not in SIGNAL_STATES or item["evidence_ref"] not in refs:
            return [], "signals require unique supported states and supplied evidence"
        rows.append({"id": item["id"], "status": item["status"], "note": item.get("note", "not_reported"), "evidence_ref": item["evidence_ref"]})
        ids.add(item["id"])
    return rows, None


def _reprioritization(raw: Any, objective_ids: set[str], refs: set[str]) -> tuple[dict[str, Any], str | None]:
    if raw is None:
        return {"status": "not_reported"}, None
    if not isinstance(raw, dict) or raw.get("status") != "proposed":
        return {"status": "not_reported"}, "reprioritization must be a proposed owner-review record"
    affected = raw.get("objective_refs")
    evidence_ref = raw.get("evidence_ref")
    if not isinstance(raw.get("rationale"), str) or not raw["rationale"].strip() or not isinstance(affected, list) or not affected:
        return {"status": "not_reported"}, "reprioritization requires rationale and objective_refs"
    if any(ref not in objective_ids for ref in affected) or evidence_ref not in refs:
        return {"status": "not_reported"}, "reprioritization references must match supplied objectives and evidence"
    return {"status": "PROPOSED_FOR_OWNER", "rationale": raw["rationale"], "objective_refs": affected, "evidence_ref": evidence_ref, "activated": False}, None


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Normalize one planning request into a deterministic review artifact."""
    if not isinstance(request, dict):
        return _failure({}, "request must be an object")
    if request.get("mode") not in MODES:
        return _failure(request, "unknown planning mode is rejected")
    if request.get("privacy_classification") not in {"synthetic", "redacted", "public"}:
        return _failure(request, "privacy classification must be synthetic, redacted, or public")
    refs, error, statuses = _refs(request.get("source_evidence"))
    if error:
        return _failure(request, error, refs)
    if _private(request):
        return _failure(request, "private identifiers, credentials, or confidential company data are not accepted", refs)
    if request.get("requested_action") in BLOCKED_ACTIONS:
        return _failure(request, "requested action exceeds the skill authority boundary", refs)
    if request.get("horizon") not in HORIZONS:
        return _failure(request, "one supported planning horizon is required", refs)
    if not isinstance(request.get("plan_ref"), str) or not re.fullmatch(r"plan:[A-Za-z0-9][A-Za-z0-9._:-]{2,127}", request["plan_ref"]):
        return _failure(request, "a unique plan_ref is required", refs)
    if not isinstance(request.get("period"), str) or not request["period"].strip():
        return _failure(request, "a planning period is required", refs)
    objectives, error = _objective_rows(request.get("objectives"), set(refs))
    if error:
        return _failure(request, error, refs)
    uncertainty: list[str] = []
    kpis, error = _kpi_rows(request.get("kpis", []), set(refs), request["period"], uncertainty)
    if error:
        return _failure(request, error, refs)
    signals, error = _signal_rows(request.get("signals"), set(refs))
    if error:
        return _failure(request, error, refs)
    reprioritization, error = _reprioritization(request.get("reprioritization"), {row["id"] for row in objectives}, set(refs))
    if error:
        return _failure(request, error, refs)
    result = _base(request, "READY_FOR_OWNER", refs, uncertainty)
    result.update({"objectives": objectives, "kpis": kpis, "signals": signals, "reprioritization": reprioritization})
    result["uncertainty"].extend(f"{ref} is not_reported" for ref in refs if next(item for item in request["source_evidence"] if item["ref"] == ref).get("status") == "not_reported")
    if statuses == {"not_reported"} or result["uncertainty"]:
        result["status"] = "DRAFT"
    return result


def main() -> int:
    """Run the helper against stdin or a JSON file."""
    parser = argparse.ArgumentParser(description="Review supplied planning evidence without mutating Program or Task state.")
    parser.add_argument("--input", type=Path, help="JSON request path; otherwise read JSON from stdin")
    args = parser.parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        result = normalize_request(json.loads(raw))
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] != "BLOCKED" else 1
    except (OSError, json.JSONDecodeError, TypeError, ValueError, OverflowError) as exc:
        print(json.dumps(_failure({}, str(exc), ["fixture:parse"]), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
