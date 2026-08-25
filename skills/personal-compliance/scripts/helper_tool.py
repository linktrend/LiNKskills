#!/usr/bin/env python3
"""Offline deterministic helper for configurable personal-compliance plans."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from typing import Any


ROLLBACK_TARGET = (
    "ABSENT@610e5a42b2356d2da5eaea0ef95cea806f93f45e/"
    "tree:158d87825593e781e43d9a4eaaecf1259c6387e0 (no prior qualified PKT-10 release)"
)
EFFECTS = {
    "external_calls": [],
    "messages_sent": [],
    "mutations": [],
    "private_state_writes": False,
}
PRIVATE_MARKER = re.compile(
    r"(?:sk_live|bearer\s+|password\s*[:=]|access[_-]?token\s*[:=]|"
    r"api[_-]?key\s*[:=]|private[_-]?key|customer@example\.com|"
    r"/(?:Users|home|private/tmp)/|\b(?:ssn|medical_record|diagnosis)\s*[:=])",
    re.IGNORECASE,
)


def _minutes(value: str) -> int | None:
    """Convert an HH:MM value to minutes when it is a valid clock time."""

    match = re.fullmatch(r"([0-2][0-9]):([0-5][0-9])", value)
    if not match:
        return None
    hours, minutes = int(match.group(1)), int(match.group(2))
    if hours > 23:
        return None
    return hours * 60 + minutes


def _result(
    *,
    status: str,
    mode: str,
    disposition: str,
    rationale: str,
    confidence: str,
    evidence_refs: list[str],
    state: str = "NOT_APPLICABLE",
    state_reason: str = "No selfie state was requested.",
    reminders: dict[str, Any] | None = None,
    battery: dict[str, Any] | None = None,
    image: dict[str, Any] | None = None,
    measurements: dict[str, Any] | None = None,
    escalation_required: bool = False,
    escalation_reason: str = "No external action is requested.",
    owner: str = "consumer-owner",
    idempotency_key: str,
) -> dict[str, Any]:
    """Build a complete output contract with no external effects."""

    return {
        "status": status,
        "mode": mode,
        "decision": {"disposition": disposition, "rationale": rationale, "confidence": confidence},
        "disposition": disposition,
        "idempotency_key": idempotency_key,
        "evidence_refs": evidence_refs,
        "state_transition": {"state": state, "reason": state_reason},
        "reminders": reminders or {"proposed": [], "suppressed": False, "duplicate_of": ""},
        "battery_projection": battery or {
            "available": False,
            "current_percent": None,
            "projected_percent": None,
            "threshold_percent": None,
            "alert": False,
            "maintenance_cancelled": False,
            "rate_labels": [],
        },
        "image_review": image or {"image_ref": "", "confirmed": [], "confirmations_needed": [], "correction_history": []},
        "measurements": measurements or {"bundled": [], "final_checkpoint": False, "next_checkpoint_requested": False},
        "escalation": {"required": escalation_required, "reason": escalation_reason, "owner": owner},
        "effects": dict(EFFECTS),
        "rollback": ROLLBACK_TARGET,
    }


def _idempotency_key(request: dict[str, Any]) -> str:
    """Return the stable request key without retaining request contents."""

    payload = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "pc-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _selfie_state(request: dict[str, Any], config: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Apply the configurable selfie window and reminder deduplication rules."""

    selfie = request.get("selfie") or {}
    window = config.get("valid_window") or {}
    start = _minutes(window.get("start", ""))
    end = _minutes(window.get("end", ""))
    capture = selfie.get("capture_time")
    capture_minutes = _minutes(capture) if isinstance(capture, str) else None
    completion_recorded = selfie.get("completion_recorded") is True
    if start is None or end is None or start >= end:
        return "UNKNOWN", "A consumer-owned valid window is missing or invalid.", {"proposed": [], "suppressed": False, "duplicate_of": ""}
    if completion_recorded and capture_minutes is None:
        state, reason = "COMPLETED", "The consumer supplied a completion record without an image time."
    elif capture_minutes is None:
        state = "MISSED" if selfie.get("window_closed") is True else "UNKNOWN"
        reason = "The window closed without a report." if state == "MISSED" else "No capture evidence is available yet."
    elif capture_minutes < start:
        state, reason = "EARLY", "The capture occurred before the configured valid window."
    elif capture_minutes <= end:
        state, reason = "COMPLETED", "The capture occurred inside the configured valid window."
    else:
        state, reason = "REPORTED_LATE", "The capture occurred after the configured valid window."
    existing = selfie.get("existing_reminder_refs") or []
    kind = selfie.get("reminder_kind")
    if state in {"COMPLETED", "REPORTED_LATE"} or not kind:
        reminders = {"proposed": [], "suppressed": False, "duplicate_of": ""}
    elif existing:
        reminders = {"proposed": [], "suppressed": True, "duplicate_of": str(existing[0])}
    else:
        reminders = {"proposed": [f"conditional:{kind}"], "suppressed": False, "duplicate_of": ""}
    return state, reason, reminders


def _battery_projection(request: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Learn context-specific synthetic rates and make a bounded projection."""

    battery = request.get("battery") or {}
    observations = battery.get("observations") or []
    target = config.get("upper_target")
    threshold = config.get("alert_threshold")
    horizon = config.get("next_charge_hours")
    minimum = int(config.get("minimum_rate_observations", 2))
    if not isinstance(target, (int, float)) or not isinstance(threshold, (int, float)) or not isinstance(horizon, (int, float)):
        return {"available": False, "current_percent": None, "projected_percent": None, "threshold_percent": None, "alert": False, "maintenance_cancelled": False, "rate_labels": ["needs-config"]}
    if not isinstance(observations, list) or len(observations) < 2:
        return {"available": False, "current_percent": None, "projected_percent": None, "threshold_percent": threshold, "alert": False, "maintenance_cancelled": False, "rate_labels": ["needs-observations"]}
    ordered = sorted(observations, key=lambda item: float(item.get("timestamp_hours", -1)))
    if any(not isinstance(item.get("percentage"), (int, float)) or not 0 <= item["percentage"] <= 100 for item in ordered):
        return {"available": False, "current_percent": None, "projected_percent": None, "threshold_percent": threshold, "alert": False, "maintenance_cancelled": False, "rate_labels": ["invalid-observation"]}
    charge_rates_by_context: dict[str, list[float]] = {}
    discharge_rates_by_context: dict[str, list[float]] = {}
    contexts: set[str] = set()
    for before, after in zip(ordered, ordered[1:]):
        elapsed = float(after["timestamp_hours"]) - float(before["timestamp_hours"])
        if elapsed <= 0:
            continue
        context = f"{before.get('charger_key')}@{before.get('location_key')}"
        contexts.add(context)
        delta = float(after["percentage"]) - float(before["percentage"])
        if delta > 0 and after.get("plugged") is True:
            charge_rates_by_context.setdefault(context, []).append(delta / elapsed)
        elif delta < 0 and after.get("plugged") is False:
            discharge_rates_by_context.setdefault(context, []).append(abs(delta) / elapsed)
    current = float(ordered[-1]["percentage"])
    current_context = f"{ordered[-1].get('charger_key')}@{ordered[-1].get('location_key')}"
    charge_rates = charge_rates_by_context.get(current_context, [])
    discharge_rates = discharge_rates_by_context.get(current_context, [])
    labels = [f"contexts:{len(contexts)}"]
    if len(charge_rates) < minimum or len(discharge_rates) < minimum:
        labels.append("provisional-rates")
        return {"available": False, "current_percent": current, "projected_percent": None, "threshold_percent": threshold, "alert": False, "maintenance_cancelled": False, "rate_labels": labels + [f"context:{current_context}"]}
    labels.append("learned-rates")
    charge = sum(charge_rates) / len(charge_rates)
    discharge = sum(discharge_rates) / len(discharge_rates)
    # Keep the discharge risk projection for threshold alerts, while using
    # the learned charge rate and upper target as a hard saturation bound.
    # This models the bounded next-charge window without treating charging as
    # permission to suppress a consumer-owned low-battery alert.
    discharge_projection = max(0.0, round(current - discharge * float(horizon), 2))
    charge_saturation = min(float(target), round(current + charge * float(horizon), 2))
    projected = min(discharge_projection, charge_saturation)
    alert = projected <= float(threshold)
    labels.append("saturation-aware-charge-estimate")
    labels.append(f"context:{current_context}")
    labels.append("silent-no-alert" if not alert else "threshold-alert")
    return {"available": True, "current_percent": current, "projected_percent": projected, "threshold_percent": threshold, "alert": alert, "maintenance_cancelled": False, "rate_labels": labels}


def _image_review(request: dict[str, Any]) -> dict[str, Any]:
    """Preserve material ambiguity and append correction history."""

    image = request.get("image") or {}
    confirmed: list[str] = []
    confirmations: list[str] = []
    for extraction in image.get("extractions") or []:
        field, value = str(extraction.get("field", "")), str(extraction.get("value", ""))
        if extraction.get("material") is True and extraction.get("confidence") in {"low", "unknown"}:
            confirmations.append(field)
        elif field:
            confirmed.append(f"{field}={value}")
    history = []
    for correction in image.get("corrections") or []:
        field = str(correction.get("field", ""))
        if field:
            history.append(f"{field}:prior={correction.get('prior_value')};proposed={correction.get('proposed_value')};reason={correction.get('reason')}")
    return {"image_ref": str(image.get("image_ref", "")), "confirmed": confirmed, "confirmations_needed": confirmations, "correction_history": history}


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, redacted personal-compliance plan."""

    key = _idempotency_key(request)
    mode = request.get("mode", "other") if isinstance(request.get("mode", "other"), str) else "other"
    if PRIVATE_MARKER.search(json.dumps(request, sort_keys=True)) or request.get("privacy_classification") == "restricted":
        return _result(status="FAILED", mode=mode, disposition="privacy_rejected", rationale="Privacy gate rejected restricted or sensitive input before processing.", confidence="high", evidence_refs=[], escalation_required=True, escalation_reason="Replace with synthetic or redacted evidence.", idempotency_key=key)
    evidence = request.get("source_evidence")
    if not isinstance(evidence, list) or not evidence or any(not isinstance(item, dict) or not all(item.get(field) for field in ("ref", "status", "provenance", "licence")) for item in evidence):
        return _result(status="FAILED", mode=mode, disposition="needs-evidence", rationale="Evidence is missing or lacks provenance and licence.", confidence="unknown", evidence_refs=[], escalation_required=True, escalation_reason="Supply bounded evidence before reasoning.", idempotency_key=key)
    refs = [str(item["ref"]) for item in evidence]
    if any(item.get("status") in {"not_reported", "unknown"} for item in evidence):
        return _result(status="PENDING_APPROVAL", mode=mode, disposition="needs-evidence", rationale="Material evidence is not reported; no value was guessed.", confidence="unknown", evidence_refs=refs, escalation_required=True, escalation_reason="Consumer owner must supply or confirm the missing evidence.", idempotency_key=key)
    actions = request.get("requested_actions") or ["prepare"]
    if not isinstance(actions, list) or any(action not in {"read", "prepare", "record", "remind", "project", "correct", "send", "delete", "diagnose", "activate"} for action in actions):
        return _result(status="PENDING_APPROVAL", mode=mode, disposition="authority_escalation", rationale="Unknown action fails closed and cannot grant authority.", confidence="high", evidence_refs=refs, escalation_required=True, escalation_reason="Declare an allowed action and obtain owner review.", idempotency_key=key)
    if any(action in {"send", "delete", "diagnose", "activate"} for action in actions):
        return _result(status="PENDING_APPROVAL", mode=mode, disposition="authority_escalation", rationale="External delivery, deletion, diagnosis, and activation remain outside the skill.", confidence="high", evidence_refs=refs, escalation_required=True, escalation_reason="Consumer owner and owning system must review the requested effect.", idempotency_key=key)
    if mode not in {"selfie_compliance", "battery_tracking", "combined"}:
        return _result(status="PENDING_APPROVAL", mode=mode, disposition="clarification", rationale="Mode is not a declared personal-compliance workflow.", confidence="unknown", evidence_refs=refs, escalation_required=True, escalation_reason="Consumer owner must specify selfie or battery mode.", idempotency_key=key)
    config = request.get("configuration") or {}
    state, state_reason, reminders = ("NOT_APPLICABLE", "No selfie state was requested.", {"proposed": [], "suppressed": False, "duplicate_of": ""})
    if mode in {"selfie_compliance", "combined"}:
        state, state_reason, reminders = _selfie_state(request, config)
    battery = _battery_projection(request, config) if mode in {"battery_tracking", "combined"} else None
    image = _image_review(request) if request.get("image") else None
    measurements = request.get("measurements") or []
    bundled = sorted(set(str(item) for item in measurements))
    final_checkpoint = config.get("checkpoint") == "final"
    disposition = "prepared" if state not in {"UNKNOWN"} else "needs-evidence"
    status = "COMPLETED" if disposition == "prepared" else "PENDING_APPROVAL"
    if battery and not battery["available"]:
        status, disposition = "PENDING_APPROVAL", "needs-evidence"
    if state == "MISSED":
        status, disposition = "PENDING_APPROVAL", "needs-evidence"
    return _result(status=status, mode=mode, disposition=disposition, rationale="Prepared a configurable, effect-free private-compliance plan.", confidence="medium" if status == "COMPLETED" else "unknown", evidence_refs=refs, state=state, state_reason=state_reason, reminders=reminders, battery=battery, image=image, measurements={"bundled": bundled, "final_checkpoint": final_checkpoint, "next_checkpoint_requested": not final_checkpoint and bool(bundled)}, escalation_required=status != "COMPLETED", escalation_reason="Consumer owner must resolve missing evidence or state." if status != "COMPLETED" else "No external action is requested.", idempotency_key=key)


def main() -> int:
    """Read one JSON object from stdin and emit one JSON result."""

    try:
        value = json.load(sys.stdin)
        if not isinstance(value, dict):
            safe = {"invalid_input_type": type(value).__name__}
            result = _result(status="FAILED", mode="other", disposition="invalid-input", rationale="Input must be a JSON object; no processing occurred.", confidence="high", evidence_refs=[], escalation_required=True, escalation_reason="Provide one object matching the input contract.", idempotency_key=_idempotency_key(safe))
            print(json.dumps(result, sort_keys=True))
            return 1
        print(json.dumps(normalize_request(value), sort_keys=True))
        return 0
    except Exception:  # structured, non-sensitive CLI failure
        safe = {"invalid_input": "malformed"}
        result = _result(status="FAILED", mode="other", disposition="invalid-input", rationale="Input could not be parsed or validated; no processing occurred.", confidence="high", evidence_refs=[], escalation_required=True, escalation_reason="Provide one object matching the input contract.", idempotency_key=_idempotency_key(safe))
        print(json.dumps(result, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
