#!/usr/bin/env python3
"""Deterministic, private-only health tracking helper.

The helper accepts synthetic or redacted observations and emits a bounded
draft. It never calls a service, writes a record, creates a reminder, or
exports detailed health data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any


ROLLBACK = "ABSENT@610e5a42b2356d2da5eaea0ef95cea806f93f45e/tree:158d87825593e781e43d9a4eaaecf1259c6387e0"
ALLOWED_MODES = {
    "initial_assessment", "monthly_assessment", "checkpoint", "hydration",
    "treatment_appointment", "nutrition", "meal_photo", "exercise", "sleep",
    "measurement", "bowel", "calendar_reminder", "capacity_export",
}
PRIVATE_MARKERS = (
    "customer@example.com", "@example.com", "password", "api_key", "access_token",
    "private key", "BEGIN PRIVATE KEY", "social security", "phone number",
)
SPOT_REDUCTION_MARKERS = ("spot reduction", "lose belly fat", "target fat", "guaranteed waist")


def _effects() -> dict[str, list[Any]]:
    """Return the immutable empty-effects contract."""
    return {
        "external_calls": [],
        "mutations": [],
        "calendar_reminders": [],
        "messages_sent": [],
        "data_exports": [],
    }


def _base(mode: str, refs: list[str], status: str = "COMPLETED") -> dict[str, Any]:
    """Create a stable output envelope with private destination metadata."""
    return {
        "status": status,
        "mode": mode,
        "observations": [],
        "evidence": refs or ["evidence:missing"],
        "uncertainty": [],
        "next_actions": [],
        "effects": _effects(),
        "privacy": {
            "destination": "private_consumer_store",
            "detailed_data_retained": True,
            "exportable_fields": [],
        },
        "rollback": ROLLBACK,
    }


def _failure(mode: str, reason: str, refs: list[str]) -> dict[str, Any]:
    """Return a fail-closed result without echoing sensitive input."""
    result = _base(mode, refs, "FAILED")
    result["uncertainty"] = [reason]
    result["next_actions"] = ["Provide the missing safe evidence or ask the private owner to review."]
    return result


def _pending(mode: str, reason: str, refs: list[str]) -> dict[str, Any]:
    """Return an owner-review result without granting authority."""
    result = _base(mode, refs, "PENDING_REVIEW")
    result["uncertainty"] = [reason]
    result["next_actions"] = ["Route the bounded question to the private owner; do not apply an external action."]
    return result


def _refs(raw: Any) -> tuple[list[str], str | None]:
    """Validate source evidence and return safe references only."""
    if not isinstance(raw, list) or not raw:
        return [], "source_evidence must contain at least one reference"
    refs: list[str] = []
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
            return [], "each source evidence item requires a reference"
        ref = item["ref"]
        if not re.fullmatch(r"(?:fixture|source|consumer):[^\s]+", ref):
            return [], "source references must be fixture, source, or consumer references"
        if item.get("status") not in {"confirmed", "reported", "not_reported"}:
            return [], "each source evidence item requires an explicit status"
        refs.append(ref)
    return refs, None


def _has_private_marker(value: Any) -> bool:
    """Detect obvious private or credential markers without retaining content."""
    text = json.dumps(value, sort_keys=True, ensure_ascii=False).lower()
    return any(marker.lower() in text for marker in PRIVATE_MARKERS)


def _add(result: dict[str, Any], field: str, value: Any, status: str, refs: list[str]) -> None:
    """Append one evidence-linked observation."""
    result["observations"].append({"field": field, "value": value, "status": status, "evidence_refs": refs})


def _not_reported_fields(result: dict[str, Any], data: dict[str, Any], refs: list[str]) -> None:
    """Preserve absent routine fields instead of guessing them."""
    for field in ("energy", "mood", "stress", "capacity_state"):
        _add(result, field, data.get(field, "not_reported"), "not_reported" if field not in data else "reported", refs)


def _sleep_minutes(start: str, end: str) -> int:
    """Calculate a bounded sleep duration from ISO timestamps."""
    begin = dt.datetime.fromisoformat(start.replace("Z", "+00:00"))
    finish = dt.datetime.fromisoformat(end.replace("Z", "+00:00"))
    if begin.tzinfo is None or finish.tzinfo is None:
        raise ValueError("sleep timestamps require timezone offsets")
    if finish < begin:
        finish += dt.timedelta(days=1)
    minutes = int((finish - begin).total_seconds() // 60)
    if minutes <= 0 or minutes > 24 * 60:
        raise ValueError("sleep duration must be between 1 and 1440 minutes")
    return minutes


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Normalize one request into a deterministic, side-effect-free result."""
    if not isinstance(request, dict):
        return _failure("unknown", "request must be an object", [])
    mode = request.get("mode")
    if mode not in ALLOWED_MODES:
        return _failure(str(mode or "unknown"), "unknown mode is rejected", [])
    if request.get("privacy_classification") not in {"synthetic", "redacted_private_snapshot"}:
        return _failure(mode, "privacy classification must be synthetic or redacted_private_snapshot", [])
    refs, error = _refs(request.get("source_evidence"))
    if error:
        return _failure(mode, error, refs)
    if _has_private_marker(request):
        return _failure(mode, "private identifiers or credentials are not accepted", refs)
    data = request.get("data", {})
    if not isinstance(data, dict):
        return _failure(mode, "data must be an object", refs)
    known = set(data.get("known_answers", []))
    requested = set(data.get("requested_questions", []))
    repeated = sorted(known.intersection(requested))
    if repeated:
        return _failure(mode, "known question requested again: " + ", ".join(repeated), refs)
    result = _base(mode, refs)

    if mode in {"initial_assessment", "monthly_assessment"}:
        _not_reported_fields(result, data, refs)
    elif mode == "checkpoint":
        checkpoint_number = data.get("checkpoint_number")
        if isinstance(checkpoint_number, bool) or not isinstance(checkpoint_number, int) or not 1 <= checkpoint_number <= 3:
            return _failure(mode, "checkpoint_number 1-3 is required", refs)
        for field in ("energy", "mood", "stress"):
            value = data.get(field, "not_reported")
            if value != "not_reported" and (not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5):
                return _failure(mode, f"{field} must be a separate integer from 1 to 5 or not_reported", refs)
            _add(result, field, value, "not_reported" if value == "not_reported" else "reported", refs)
        capacity = data.get("capacity_state", "not_reported")
        if capacity not in {"low", "steady", "available", "not_reported"}:
            return _failure(mode, "capacity_state must be low, steady, available, or not_reported", refs)
        _add(result, "capacity_state", capacity, "not_reported" if capacity == "not_reported" else "reported", refs)
        result["capacity_state"] = capacity
    elif mode == "hydration":
        bottle, remaining = data.get("bottle_ml"), data.get("remaining_ml")
        if not isinstance(bottle, (int, float)) or not isinstance(remaining, (int, float)) or bottle < 0 or remaining < 0 or remaining > bottle:
            return _failure(mode, "bottle_ml and remaining_ml must be non-negative with remaining no greater than bottle", refs)
        consumed = bottle - remaining
        _add(result, "consumed_ml", consumed, "confirmed", refs)
    elif mode == "treatment_appointment":
        record = data.get("treatment_record")
        if not isinstance(record, dict) or record.get("kind") not in {"appointment", "dose", "dose_change_question"}:
            return _failure(mode, "a bounded appointment, dose, or dose-change record is required", refs)
        _add(result, "treatment_record_kind", record["kind"], "reported", refs)
        result = _pending(mode, "treatment and dose decisions require owner review and are never applied", refs) | {"observations": result["observations"]}
    elif mode == "nutrition":
        estimate = data.get("protein_estimate_g")
        if estimate is not None and (not isinstance(estimate, (int, float)) or estimate < 0 or not data.get("estimate_basis") or not data.get("estimate_uncertainty")):
            return _failure(mode, "nutrition estimates require a non-negative value, basis, and uncertainty", refs)
        _add(result, "protein_estimate_g", estimate if estimate is not None else "not_reported", "estimated" if estimate is not None else "not_reported", refs)
        if estimate is not None:
            result["uncertainty"].append(str(data["estimate_uncertainty"]))
    elif mode == "meal_photo":
        if not data.get("meal_reference") and not data.get("photo_reference"):
            return _failure(mode, "a synthetic or redacted meal/photo reference is required", refs)
        if data.get("photo_reference") and not data.get("image_uncertainty"):
            return _failure(mode, "material image uncertainty must be recorded", refs)
        _add(result, "meal_reference", data.get("meal_reference", "not_reported"), "reported", refs)
        if data.get("photo_reference"):
            _add(result, "photo_reference", data["photo_reference"], "reported", refs)
            result["uncertainty"].append(data["image_uncertainty"])
        if data.get("correction"):
            _add(result, "correction", data["correction"], "reported", refs)
    elif mode == "exercise":
        proposal = str(data.get("exercise_proposal", ""))
        if not data.get("exercise_evidence") or not proposal:
            return _failure(mode, "exercise proposals require evidence and a proposal", refs)
        if any(marker in proposal.lower() for marker in SPOT_REDUCTION_MARKERS):
            return _failure(mode, "spot-reduction and guaranteed body-area claims are rejected", refs)
        _add(result, "exercise_proposal", proposal, "proposed", refs + list(data["exercise_evidence"]))
        result["next_actions"] = ["Private owner reviews the evidence-backed proposal."]
    elif mode == "sleep":
        try:
            minutes = _sleep_minutes(str(data.get("sleep_start", "")), str(data.get("sleep_end", "")))
        except (TypeError, ValueError) as exc:
            return _failure(mode, str(exc), refs)
        _add(result, "sleep_duration_minutes", minutes, "confirmed", refs)
    elif mode == "measurement":
        if data.get("measurement_kind") not in {"scale", "waist", "bowel"} or not isinstance(data.get("measurement_value"), (int, float)) or not data.get("device") or not data.get("measurement_source"):
            return _failure(mode, "measurement kind, value, device, and source are required and remain separate", refs)
        _add(result, data["measurement_kind"], data["measurement_value"], "reported", refs)
        result["uncertainty"].append(f"device={data['device']}; source={data['measurement_source']}")
    elif mode == "bowel":
        if not data.get("bowel_observation") or not data.get("measurement_source"):
            return _failure(mode, "bowel observation and source are required", refs)
        _add(result, "bowel_observation", data["bowel_observation"], "reported", refs)
    elif mode == "calendar_reminder":
        if not data.get("reminder_key") or not data.get("reminder_at"):
            return _failure(mode, "reminder_key and reminder_at are required for deduplication", refs)
        _add(result, "reminder_key", data["reminder_key"], "proposed", refs)
        result = _pending(mode, "calendar reminder remains a deduplicated private proposal; no calendar is called", refs) | {"observations": result["observations"]}
    elif mode == "capacity_export":
        capacity = data.get("capacity_state")
        if data.get("export_capacity_state") is not True or capacity not in {"low", "steady", "available", "not_reported"}:
            return _failure(mode, "only an explicitly requested capacity_state may be exported", refs)
        result["capacity_state"] = capacity
        result["privacy"]["exportable_fields"] = ["capacity_state"]
        _add(result, "capacity_state", capacity, "reported", refs)
    if data.get("safety_concern"):
        result = _pending(mode, "a supplied safety concern requires the owner-defined review path", refs) | {"observations": result["observations"]}
    return result


def main() -> int:
    """Run the helper against stdin or a JSON file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON request path; otherwise read stdin")
    args = parser.parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        request = json.loads(raw)
        result = normalize_request(request)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] != "FAILED" else 1
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps(_failure("unknown", str(exc), ["evidence:parse"]), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
