#!/usr/bin/env python3
"""Deterministic, side-effect-free Agent Workforce Management helper."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable


ROLLBACK = "ABSENT@517f22ee135c298a17a74f84a84b60accdf22cf4/tree:d2514ee298074c70f9bb5fb19f2fc71af7d43f16"
MODES = {"role_definition", "rule_selection", "capability_request", "delegation_plan", "workforce_review", "quality_review", "suspend_proposal", "retire_proposal"}
BLOCKED_ACTIONS = {"activate", "suspend", "retire", "approve_grant", "copy_credentials", "copy_private_memory", "unknown"}
PRIVATE_MARKERS = ("customer@example.com", "password", "api_key", "access_token", "private key", "private memory", "private_memory", "credential", "oauth", "cookie", "secret token")
EVIDENCE_REF = re.compile(r"(?:fixture|source|consumer):[^\s]+$")
OWNER_REF = re.compile(r"(?:owner|consumer):[^\s]+$")


def _effects() -> dict[str, list[Any]]:
    """Return the immutable empty-effects contract."""
    return {"messages_sent": [], "external_calls": [], "mutations": []}


def _valid_scalar(value: Any, pattern: re.Pattern[str] | None = None) -> bool:
    """Check a non-empty bounded string and an optional reference pattern."""
    return isinstance(value, str) and bool(value.strip()) and (pattern is None or bool(pattern.fullmatch(value)))


def _base(request: dict[str, Any], status: str, refs: list[str], uncertainty: list[str] | None = None, include_data: bool = False) -> dict[str, Any]:
    """Create an output envelope without echoing unsafe or invalid input."""
    mode = request.get("mode") if _valid_scalar(request.get("mode")) else "unknown"
    workforce_ref = request.get("workforce_ref") if _valid_scalar(request.get("workforce_ref"), re.compile(r"^workforce:[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")) else "workforce:unknown"
    role = request.get("role") if include_data and isinstance(request.get("role"), dict) else None
    rule = request.get("rule_selection") if include_data and isinstance(request.get("rule_selection"), dict) else None
    arrays = {key: list(request.get(key) or []) if include_data and isinstance(request.get(key) or [], list) else [] for key in ("capability_requests", "delegations", "workload", "quality", "proposals")}
    owner_ref = "not_reported"
    if isinstance(role, dict) and isinstance(role.get("owner_ref"), str):
        owner_ref = role["owner_ref"]
    recommendation = request.get("recommendation") if include_data and _valid_scalar(request.get("recommendation")) else "Recommendation not reported"
    return {
        "status": status,
        "mode": mode,
        "workforce_ref": workforce_ref,
        "role": role,
        "rule_selection": rule,
        **arrays,
        "recommendation": recommendation,
        "evidence": refs or ["fixture:missing"],
        "uncertainty": list(uncertainty or []),
        "authority": {"owner_ref": owner_ref, "grants_approved": False, "agents_activated": False, "agents_suspended": False, "agents_retired": False},
        "effects": _effects(),
        "rollback": ROLLBACK,
    }


def _failure(request: dict[str, Any], reason: str, refs: list[str] | None = None) -> dict[str, Any]:
    """Return a safe blocked result with a typed reason and no nested echo."""
    return _base(request if isinstance(request, dict) else {}, "BLOCKED", refs or [], [reason], include_data=False)


def _refs(raw: Any) -> tuple[list[str], str | None, list[str]]:
    """Validate evidence references, statuses, and uniqueness."""
    if not isinstance(raw, list) or not raw:
        return [], "source_evidence must contain at least one reference", []
    refs: list[str] = []
    uncertain: list[str] = []
    for item in raw:
        if not isinstance(item, dict) or not _valid_scalar(item.get("ref"), EVIDENCE_REF):
            return [], "each source evidence item requires a namespaced reference", refs
        if item.get("status") not in {"confirmed", "reported", "not_reported"}:
            return [], "each source evidence item requires an explicit status", refs
        ref = item["ref"]
        if ref in refs:
            return [], "duplicate evidence references are rejected", refs
        refs.append(ref)
        if item["status"] == "not_reported":
            uncertain.append(f"{ref} is not_reported")
    return refs, None, uncertain


def _private(value: Any) -> bool:
    """Detect obvious private, credential, or account material without retaining it."""
    blob = json.dumps(value, sort_keys=True, ensure_ascii=False).lower()
    return any(marker in blob for marker in PRIVATE_MARKERS)


def _evidence_ref(value: Any, refs: set[str]) -> bool:
    """Require a valid evidence pointer already supplied by the caller."""
    return _valid_scalar(value, EVIDENCE_REF) and value in refs


def _role(value: Any, refs: set[str]) -> str | None:
    """Validate a reusable role definition."""
    if not isinstance(value, dict) or set(value) - {"role_ref", "purpose", "domain", "boundary", "owner_ref", "evidence_ref"}:
        return "role definition fields are invalid"
    if not _valid_scalar(value.get("role_ref"), re.compile(r"^role:[^\s]+$")) or not all(_valid_scalar(value.get(key)) for key in ("purpose", "domain", "boundary")):
        return "role requires role_ref, purpose, domain, and boundary"
    if not _valid_scalar(value.get("owner_ref"), OWNER_REF) or not _evidence_ref(value.get("evidence_ref"), refs):
        return "role owner_ref or evidence_ref is invalid"
    return None


def _rule(value: Any, refs: set[str]) -> str | None:
    """Validate a supplied Brain-rule applicability record."""
    if not isinstance(value, dict) or set(value) - {"rule_ref", "applicability", "evidence_ref"}:
        return "rule selection fields are invalid"
    if not _valid_scalar(value.get("rule_ref"), re.compile(r"^rule:[^\s]+$")) or value.get("applicability") not in {"applicable", "not_applicable", "uncertain"} or not _evidence_ref(value.get("evidence_ref"), refs):
        return "rule selection requires a supplied rule, applicability, and evidence"
    return None


def _records(raw: Any, name: str, refs: set[str], validator: Callable[[dict[str, Any], set[str]], str | None], key: str) -> tuple[list[dict[str, Any]], str | None]:
    """Validate a bounded list and reject duplicate identifiers."""
    if not isinstance(raw, list):
        return [], f"{name} must be a list"
    result: list[dict[str, Any]] = []
    ids: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            return [], f"{name} contains an invalid item"
        error = validator(item, refs)
        if error:
            return [], error
        identifier = item.get(key)
        if identifier in ids:
            return [], f"duplicate {name} identifiers are rejected"
        ids.add(identifier)
        result.append(item)
    return result, None


def _capability(item: dict[str, Any], refs: set[str]) -> str | None:
    """Validate a bounded capability request."""
    if set(item) - {"capability_ref", "purpose", "evidence_ref"} or not _valid_scalar(item.get("capability_ref"), re.compile(r"^capability:[^\s]+$")) or not _valid_scalar(item.get("purpose")) or not _evidence_ref(item.get("evidence_ref"), refs):
        return "capability request requires a bounded reference, purpose, and supplied evidence"
    return None


def _delegation(item: dict[str, Any], refs: set[str]) -> str | None:
    """Validate an owner-scoped domain delegation proposal."""
    if set(item) - {"delegation_ref", "domain", "owner_ref", "status", "evidence_ref"} or not _valid_scalar(item.get("delegation_ref"), re.compile(r"^delegation:[^\s]+$")) or not _valid_scalar(item.get("domain")) or not _valid_scalar(item.get("owner_ref"), OWNER_REF) or item.get("status") not in {"proposed", "confirmed", "blocked", "not_reported"} or not _evidence_ref(item.get("evidence_ref"), refs):
        return "delegation requires domain, owner, status, and supplied evidence"
    return None


def _workload(item: dict[str, Any], refs: set[str]) -> str | None:
    """Validate bounded workload and blocker references."""
    if set(item) - {"agent_ref", "load_state", "blocker_refs", "evidence_ref"} or not _valid_scalar(item.get("agent_ref"), re.compile(r"^agent:[^\s]+$")) or item.get("load_state") not in {"available", "balanced", "overloaded", "blocked", "not_reported"} or not isinstance(item.get("blocker_refs"), list) or any(not _valid_scalar(ref, EVIDENCE_REF) for ref in item["blocker_refs"]) or not _evidence_ref(item.get("evidence_ref"), refs):
        return "workload requires agent, bounded load state, blocker references, and evidence"
    return None


def _quality(item: dict[str, Any], refs: set[str]) -> str | None:
    """Validate observed quality and repeated-failure count."""
    if set(item) - {"agent_ref", "outcome", "repeated_failure_count", "evidence_ref"} or not _valid_scalar(item.get("agent_ref"), re.compile(r"^agent:[^\s]+$")) or item.get("outcome") not in {"passed", "degraded", "failed", "not_reported"} or not isinstance(item.get("repeated_failure_count"), int) or isinstance(item.get("repeated_failure_count"), bool) or item["repeated_failure_count"] < 0 or not _evidence_ref(item.get("evidence_ref"), refs):
        return "quality requires agent, observed outcome, failure count, and evidence"
    return None


def _proposal(item: dict[str, Any], refs: set[str]) -> str | None:
    """Validate an owner-review training, review, suspend, or retire proposal."""
    if set(item) - {"proposal_ref", "agent_ref", "kind", "status", "reason", "evidence_ref"} or not _valid_scalar(item.get("proposal_ref"), re.compile(r"^proposal:[^\s]+$")) or not _valid_scalar(item.get("agent_ref"), re.compile(r"^agent:[^\s]+$")) or item.get("kind") not in {"training", "skill_review", "authority_review", "suspend", "retire"} or item.get("status") != "proposed" or not _valid_scalar(item.get("reason")) or not _evidence_ref(item.get("evidence_ref"), refs):
        return "proposal requires proposed status, bounded reason, agent, and evidence"
    return None


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Normalize one workforce request into an owner-review artifact."""
    if not isinstance(request, dict):
        return _failure({}, "request must be an object")
    if request.get("mode") not in MODES:
        return _failure(request, "unknown mode is rejected")
    if request.get("privacy_classification") not in {"synthetic", "redacted", "public"}:
        return _failure(request, "privacy classification must be synthetic, redacted, or public")
    refs, error, uncertainty = _refs(request.get("source_evidence"))
    if error:
        return _failure(request, error, refs)
    if not _valid_scalar(request.get("workforce_ref"), re.compile(r"^workforce:[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")):
        return _failure(request, "a unique workforce_ref is required", refs)
    if _private(request):
        return _failure(request, "credentials, private memory, identity, or account material is not accepted", refs)
    if request.get("requested_action") in BLOCKED_ACTIONS:
        return _failure(request, "the requested action exceeds the workforce authority boundary", refs)
    evidence = set(refs)
    if request.get("role") is not None:
        error = _role(request.get("role"), evidence)
        if error:
            return _failure(request, error, refs)
    if request.get("rule_selection") is not None:
        error = _rule(request.get("rule_selection"), evidence)
        if error:
            return _failure(request, error, refs)
        if request["rule_selection"]["applicability"] == "uncertain":
            uncertainty.append("rule applicability is uncertain")
    capabilities, error = _records(request.get("capability_requests") or [], "capability requests", evidence, _capability, "capability_ref")
    if error:
        return _failure(request, error, refs)
    delegations, error = _records(request.get("delegations") or [], "delegations", evidence, _delegation, "delegation_ref")
    if error:
        return _failure(request, error, refs)
    workload, error = _records(request.get("workload") or [], "workload", evidence, _workload, "agent_ref")
    if error:
        return _failure(request, error, refs)
    quality, error = _records(request.get("quality") or [], "quality", evidence, _quality, "agent_ref")
    if error:
        return _failure(request, error, refs)
    proposals, error = _records(request.get("proposals") or [], "proposals", evidence, _proposal, "proposal_ref")
    if error:
        return _failure(request, error, refs)
    requirements = {
        "role_definition": (request.get("role"), "role is required for role_definition"),
        "rule_selection": (request.get("rule_selection"), "rule_selection is required for rule_selection"),
        "capability_request": (capabilities, "at least one capability request is required"),
        "delegation_plan": (delegations, "at least one delegation is required"),
        "workforce_review": (workload, "at least one workload observation is required"),
        "quality_review": (quality, "at least one quality observation is required"),
        "suspend_proposal": (proposals, "at least one proposal is required"),
        "retire_proposal": (proposals, "at least one proposal is required"),
    }
    required, missing_reason = requirements[request["mode"]]
    if not required:
        return _failure(request, missing_reason, refs)
    if request["mode"] == "suspend_proposal" and any(item["kind"] != "suspend" for item in proposals):
        return _failure(request, "suspend_proposal requires suspend proposals", refs)
    if request["mode"] == "retire_proposal" and any(item["kind"] != "retire" for item in proposals):
        return _failure(request, "retire_proposal requires retire proposals", refs)
    uncertainty.extend(f"{item['agent_ref']} load is {item['load_state']}" for item in workload if item["load_state"] == "not_reported")
    uncertainty.extend(f"{item['agent_ref']} quality is not_reported" for item in quality if item["outcome"] == "not_reported")
    uncertainty.extend(f"{item['delegation_ref']} status is not_reported" for item in delegations if item["status"] == "not_reported")
    result = _base(request, "DRAFT" if uncertainty else "READY_FOR_OWNER", refs, uncertainty, include_data=True)
    result["capability_requests"] = capabilities
    result["delegations"] = delegations
    result["workload"] = workload
    result["quality"] = quality
    result["proposals"] = proposals
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
