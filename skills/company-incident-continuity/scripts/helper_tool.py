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



def _risk_result(request: dict[str, Any], status: str, risks: list[dict[str, Any]], gaps: list[str]) -> dict[str, Any]:
    """Build a risk-only envelope; never add incident identity/state/closure fields."""
    # Only validated success data is echoed. Error paths never copy untrusted input.
    if status == "NEEDS_CONTEXT":
        scope_ref, as_of = "not_reported", "not_reported"
    else:
        scope_ref = request["scope_ref"]
        as_of = request["as_of"]
    return {
        "status": status, "mode": "prospective_risk_register", "scope_ref": scope_ref,
        "as_of": as_of, "risks": risks, "assumptions": [], "gaps": list(dict.fromkeys(gaps)),
        "owner_supplied_rating_scale_or_unknown_reason": request["owner_supplied_rating_scale_or_unknown_reason"] if status != "NEEDS_CONTEXT" else {"unknown_reason": "Input was not accepted."},
        "owner_supplied_tolerance_or_unknown_reason": request["owner_supplied_tolerance_or_unknown_reason"] if status != "NEEDS_CONTEXT" else {"unknown_reason": "Input was not accepted."},
        "owner_decisions": ["Accountable owner must review treatment and decide risk acceptance; none is applied."],
        "effects": _effects(), "risk_acceptance_or_control_activation": False,
    }


def _risk_needs_context(request: dict[str, Any], reason: str) -> dict[str, Any]:
    """Return a non-echoing risk-only missing/invalid-input result."""
    return _risk_result(request if isinstance(request, dict) else {}, "NEEDS_CONTEXT", [], [reason])


def _has_explicit_unknown_reason(value: Any) -> bool:
    """Require the exact Unknown marker and a nonempty reason after it."""
    if not isinstance(value, str):
        return False
    marker, separator, reason = value.partition(":")
    return marker == "Unknown" and bool(separator) and bool(reason.strip())


def _normalize_risk_register(request: dict[str, Any]) -> dict[str, Any]:
    """Normalize supplied prospective risk facts without creating ratings or actions."""
    from jsonschema import Draft202012Validator
    definitions=json.loads((Path(__file__).resolve().parents[1]/"references/schemas.json").read_text())["definitions"]
    if list(Draft202012Validator({"$ref":"#/definitions/risk_register_input","definitions":definitions}).iter_errors(request)):
        return _risk_needs_context(request, "risk input does not match the bounded schema")
    supported = {"mode", "privacy_classification", "scope_ref", "as_of", "accountable_owner_ref", "risk_sources_and_evidence_refs", "owner_supplied_rating_scale_or_unknown_reason", "owner_supplied_tolerance_or_unknown_reason", "candidate_risks"}
    if set(request) - supported:
        return _risk_needs_context(request, "risk request contains fields outside the supported contract")
    if request.get("privacy_classification") not in {"synthetic", "redacted", "public"}:
        return _risk_needs_context(request, "privacy classification is missing or unsupported")
    if _private(request):
        return _risk_needs_context(request, "private or credential-bearing evidence is not accepted")
    scope_ref = request.get("scope_ref")
    as_of = request.get("as_of")
    owner_ref = request.get("accountable_owner_ref")
    ref_pattern = r"(?:fixture|source|consumer):[^\s]+"
    owner_pattern = r"(?:owner|consumer):[^\s]+"
    if not isinstance(scope_ref, str) or not re.fullmatch(ref_pattern, scope_ref):
        return _risk_needs_context(request, "scope_ref must identify the reviewed scope")
    if not isinstance(as_of, str) or len(as_of) < 10:
        return _risk_needs_context(request, "as_of date is required")
    if not isinstance(owner_ref, str) or not re.fullmatch(owner_pattern, owner_ref):
        return _risk_needs_context(request, "accountable_owner_ref is required")
    evidence_refs, error, unknown_refs = _refs(request.get("risk_sources_and_evidence_refs"))
    if error:
        return _risk_needs_context(request, error)
    if len(evidence_refs) > 64:
        return _risk_needs_context(request, "risk_sources_and_evidence_refs exceeds the supported bound")
    evidence_by_ref = {item["ref"]: item for item in request["risk_sources_and_evidence_refs"]}

    def basis(value: Any, ref_key: str) -> tuple[str | None, str | None]:
        if not isinstance(value, dict):
            return None, "supply an owner reference or explicit unknown reason"
        if set(value) == {ref_key, "description"}:
            ref = value.get(ref_key)
            description = value.get("description")
            if isinstance(ref, str) and re.fullmatch(ref_pattern, ref) and ref in evidence_by_ref and evidence_by_ref[ref].get("status") != "not_reported" and isinstance(description, str) and description.strip() and len(description) <= 500:
                return ref, None
            return None, "owner scale/tolerance reference must resolve to supplied evidence"
        if set(value) == {"unknown_reason"} and isinstance(value.get("unknown_reason"), str) and value["unknown_reason"].strip():
            return None, None
        return None, "supply exactly an owner reference plus description or an explicit unknown reason"

    scale_ref, error = basis(request.get("owner_supplied_rating_scale_or_unknown_reason"), "scale_ref")
    if error:
        return _risk_needs_context(request, error)
    tolerance_ref, error = basis(request.get("owner_supplied_tolerance_or_unknown_reason"), "tolerance_ref")
    if error:
        return _risk_needs_context(request, error)
    candidates = request.get("candidate_risks")
    if not isinstance(candidates, list) or not candidates or len(candidates) > 64:
        return _risk_needs_context(request, "candidate_risks must contain at least one evidence-backed risk")

    seen_ids: set[str] = set()
    seen_tuples: set[tuple[str, str, str]] = set()
    risks: list[dict[str, Any]] = []
    gaps: list[str] = []
    unknown_inherent_rating_present = False
    if scale_ref is None:
        gaps.append("Owner rating scale is not reported; no rating is assigned.")
    if tolerance_ref is None:
        gaps.append("Owner tolerance is not reported; no acceptance decision is made.")
    for item in candidates:
        required = ("id", "cause", "event", "consequence", "owner_ref", "evidence_refs")
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in required[:-1]):
            return _risk_needs_context(request, "each candidate risk needs id, cause, event, consequence, and owner_ref")
        if set(item) - {"id", "cause", "event", "consequence", "owner_ref", "evidence_refs", "current_controls", "assessment"}:
            return _risk_needs_context(request, "candidate risk contains fields outside the supported contract")
        if any(len(item[k]) > 1000 for k in ("cause", "event", "consequence")):
            return _risk_needs_context(request, "candidate risk statement exceeds the supported length")
        if not re.fullmatch(r"risk:[A-Za-z0-9][A-Za-z0-9._:-]{2,63}", item["id"]) or not re.fullmatch(owner_pattern, item["owner_ref"]):
            return _risk_needs_context(request, "candidate risk id or owner_ref is invalid")
        if item["id"] in seen_ids:
            return _risk_needs_context(request, "duplicate candidate risk id")
        identity = tuple(" ".join(item[k].casefold().split()) for k in ("cause", "event", "consequence"))
        if identity in seen_tuples:
            return _risk_needs_context(request, "duplicate cause/event/consequence requires owner resolution")
        refs = item.get("evidence_refs")
        if not isinstance(refs, list) or not refs or len(refs) > 32 or any(not isinstance(ref, str) for ref in refs):
            return _risk_needs_context(request, "each risk evidence_refs entry must resolve to supplied source evidence")
        if len(set(refs)) != len(refs) or any(ref not in evidence_by_ref for ref in refs):
            return _risk_needs_context(request, "each risk evidence_refs entry must resolve to supplied source evidence")
        controls = item.get("current_controls", [])
        if not isinstance(controls, list) or len(controls) > 32:
            return _risk_needs_context(request, "current_controls must be an array")
        normalized_controls = []
        control_refs: list[str] = []
        for control in controls:
            if not isinstance(control, dict) or set(control) - {"control_ref", "status", "evidence_refs"} or not isinstance(control.get("control_ref"), str) or not control["control_ref"].strip() or len(control["control_ref"]) > 256 or control.get("status") not in {"designed", "owner_reported_operating", "unknown"}:
                return _risk_needs_context(request, "each control needs a reference and supported owner-reported status")
            control_evidence = control.get("evidence_refs", [])
            if not isinstance(control_evidence, list) or len(control_evidence) > 32 or any(not isinstance(ref, str) for ref in control_evidence):
                return _risk_needs_context(request, "control evidence_refs must resolve to supplied source evidence")
            if len(set(control_evidence)) != len(control_evidence) or any(ref not in evidence_by_ref for ref in control_evidence):
                return _risk_needs_context(request, "control evidence_refs must resolve to supplied source evidence")
            status = control["status"]
            if status == "owner_reported_operating" and (not control_evidence or all(evidence_by_ref[ref].get("status") == "not_reported" for ref in control_evidence)):
                status = "unknown"
                gaps.append("Control operating status lacks evidence and remains unknown.")
            normalized_controls.append({"control_ref": control["control_ref"], "status": status, "evidence_refs": control_evidence})
            control_refs.extend(control_evidence)
        assessment = item.get("assessment")
        if assessment is not None:
            assessment_fields = {"origin", "likelihood_or_unknown_reason", "impact_or_unknown_reason", "inherent_rating_or_unknown_reason", "treatment_proposal", "review_trigger", "review_date_or_unknown_reason", "residual_statement_or_unknown_reason"}
            if not isinstance(assessment, dict) or set(assessment) != assessment_fields:
                return _risk_needs_context(request, "assessment must match the bounded owner/advisory assessment contract")
            if assessment.get("origin") not in {"caller_advisory", "owner_supplied"} or any(not isinstance(assessment.get(key), str) or not assessment[key].strip() or len(assessment[key]) > limit for key, limit in (("likelihood_or_unknown_reason", 1000), ("impact_or_unknown_reason", 1000), ("inherent_rating_or_unknown_reason", 1000), ("treatment_proposal", 1000), ("review_trigger", 1000), ("review_date_or_unknown_reason", 128), ("residual_statement_or_unknown_reason", 1000))):
                return _risk_needs_context(request, "assessment values must be bounded nonempty text with an explicit origin")
            raw_inherent = assessment["inherent_rating_or_unknown_reason"]
            has_unknown_reason = _has_explicit_unknown_reason(raw_inherent)
            if assessment["origin"] == "caller_advisory" and not has_unknown_reason:
                return _risk_needs_context(request, "Caller may offer qualitative rationale but may not assign an inherent rating; use Unknown: followed by a nonempty reason")
            if assessment["origin"] == "owner_supplied" and scale_ref is None and not has_unknown_reason:
                return _risk_needs_context(request, "an owner-supplied rating requires an evidenced owner scale or an explicit Unknown: reason")
            unknown_inherent_rating_present = unknown_inherent_rating_present or has_unknown_reason
        seen_ids.add(item["id"])
        seen_tuples.add(identity)
        if assessment is None:
            unknown_inherent_rating_present = True
            likelihood = "Unknown: no evidence-bounded likelihood assessment was supplied."
            impact = "Unknown: no evidence-bounded impact assessment was supplied."
            inherent = "Unknown: owner rating assessment is pending."
            treatment = "not_reported"
            review_trigger = "not_reported"
            review_date = "Unknown: no review date supplied."
            residual = "Unknown: residual risk has not been assessed."
        else:
            prefix = "Caller advisory proposal (unverified): " if assessment["origin"] == "caller_advisory" else "Owner-supplied, unverified: "
            likelihood = prefix + assessment["likelihood_or_unknown_reason"]
            impact = prefix + assessment["impact_or_unknown_reason"]
            inherent = prefix + assessment["inherent_rating_or_unknown_reason"]
            treatment = prefix + assessment["treatment_proposal"]
            review_trigger = prefix + assessment["review_trigger"]
            review_date = prefix + assessment["review_date_or_unknown_reason"]
            residual = prefix + assessment["residual_statement_or_unknown_reason"]
        risks.append({
            "id": item["id"], "cause": item["cause"], "event": item["event"],
            "consequence": item["consequence"], "owner_ref": item["owner_ref"],
            "evidence_refs": refs,
            "likelihood_or_unknown_reason": likelihood,
            "impact_or_unknown_reason": impact,
            "rating_scale_ref": scale_ref or "not_reported",
            "inherent_rating_or_unknown_reason": inherent,
            "current_controls": normalized_controls,
            "control_evidence_refs": sorted(set(control_refs)),
            "residual_rating_or_unknown_reason": residual,
            "treatment_proposal": treatment,
            "review_trigger": review_trigger,
            "review_date_or_unknown_reason": review_date,
        })
    if unknown_refs:
        gaps.append("One or more supplied evidence items are explicitly not_reported.")
    if unknown_inherent_rating_present or any("not_reported" == risk["treatment_proposal"] or risk["inherent_rating_or_unknown_reason"].startswith("Unknown:") for risk in risks):
        gaps.append("One or more likelihood/impact/rating/treatment/residual fields remain unknown or not_reported; accountable owner review is required.")
    return _risk_result(request, "DRAFT", risks, gaps)

def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Normalize one incident request into a deterministic review artifact."""
    if not isinstance(request, dict):
        return _failure({}, "request must be an object")
    if request.get("mode") == "prospective_risk_register":
        return _normalize_risk_register(request)
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
