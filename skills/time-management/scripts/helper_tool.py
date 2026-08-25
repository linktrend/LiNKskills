#!/usr/bin/env python3
"""Deterministic, offline PKT-11 planning helper.

The helper models the provider contract only. It deliberately has no database,
network, calendar, mailbox, messaging, or task-store integration.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from typing import Any


ROLLBACK_TARGET = "ABSENT@517f22ee135c298a17a74f84a84b60accdf22cf4/tree:d2514ee298074c70f9bb5fb19f2fc71af7d43f16 (no prior qualified PKT-11 release)"
EFFECTS = {"external_calls": [], "messages_sent": [], "mutations": [], "private_state_writes": False}
STATUSES = {"Provisional", "Ready", "Scheduled", "In progress", "Waiting", "Blocked", "Awaiting Carlos's update", "Awaiting for other", "Verified complete", "Completed — Carlos reported", "Cancelled", "duplicate", "created by mistake"}
PRIVATE_MARKER = re.compile(r"(?:sk_live|bearer\s+|password\s*[\"']?\s*[:=]|access[_-]?token\s*[\"']?\s*[:=]|api[_-]?key\s*[\"']?\s*[:=]|private[_-]?key|BEGIN PRIVATE KEY|secret[\"']?\s*[:=]|diagnosis[\"']?\s*[:=]|medical_record[\"']?\s*[:=]|health_cause[\"']?\s*[:=]|customer@example\.com|/(?:Users|home|private/tmp)/)", re.IGNORECASE)


def _key(request: dict[str, Any]) -> str:
    """Return a stable request key without retaining the request."""

    raw = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "tm-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _task_id(task: dict[str, Any], index: int) -> str:
    """Preserve a consumer-minted ID or produce an evaluation-only fixture ID."""

    supplied = task.get("task_id")
    if isinstance(supplied, str) and re.fullmatch(r"T-[0-9]{6}", supplied):
        return supplied
    seed = f"{task.get('title', '')}|{task.get('external_mappings', {})}|{index}"
    number = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % 999999 + 1
    return f"T-{number:06d}"


def _priority(task: dict[str, Any]) -> tuple[int, int, int, str]:
    """Sort deadlines, blockers, importance, and optional work deterministically."""

    importance = {"critical": 0, "high": 1, "normal": 2, "low": 3}.get(str(task.get("importance")), 3)
    deadline = 0 if task.get("deadline") else 1
    unblocks = 0 if task.get("unlocks") or task.get("dependencies") else 1
    return deadline, unblocks, importance, str(task.get("title", ""))


def _capacity(capacity: dict[str, Any]) -> dict[str, Any]:
    """Make a capacity decision without importing health causes."""

    state = str(capacity.get("state", "normal"))
    asks_time_off = state in {"reduced", "unavailable"}
    recommendation = {
        "high": "Use existing periods and flexible work only; do not consume breaks.",
        "normal": "Use the supplied difficulty-to-period mapping.",
        "reduced": "Ask whether time off is wanted and how long; otherwise use easier work more slowly.",
        "unavailable": "Ask whether time off is wanted and how long; protect fixed commitments only.",
        "recovered": "Treat recovered capacity as temporary and replan before normal allocation.",
    }.get(state, "Ask for a valid consumer capacity state.")
    return {"state": state, "recommendation": recommendation, "time_off_question": asks_time_off, "health_cause_included": False}


def _flexible_period(capacity: dict[str, Any]) -> dict[str, Any]:
    """Apply the five settled flexible-period checks."""

    checks = {
        "no_overdue_principal_work": not bool(capacity.get("overdue_principal_work")),
        "no_ready_current_week_task": not bool(capacity.get("ready_current_week")),
        "no_resolvable_blocker": not bool(capacity.get("resolvable_blocker")),
        "no_at_risk_deadline_or_outcome": not bool(capacity.get("deadline_at_risk")),
        "no_useful_action_before_next_workday": not bool(capacity.get("useful_action_before_next_workday")),
    }
    personal = all(checks.values())
    return {"decision": "personal" if personal else "work", "checks": checks, "reason": "All five flexible-period conditions are satisfied." if personal else "A current work, blocker, deadline, or useful action keeps the period as work."}


def _proposed_period(task: dict[str, Any], periods: list[dict[str, Any]], used: set[str]) -> str | None:
    """Choose an available matching period while preserving protected breaks."""

    difficulty = str(task.get("difficulty", "medium"))
    candidates = [p for p in periods if p.get("available", True) is not False and p.get("difficulty") in {difficulty, "flexible"} and p.get("difficulty") != "break"]
    for period in candidates:
        pid = str(period.get("period_id", ""))
        if pid not in used:
            used.add(pid)
            return pid
    return str(candidates[0].get("period_id")) if candidates else None


def _review(request: dict[str, Any]) -> dict[str, Any]:
    """Return review boundaries; acknowledgement is never inferred."""

    review = request.get("review") or {}
    known = review.get("result_known") is True
    outcomes = [str(item) for item in review.get("outcomes", []) if isinstance(item, str)]
    return {
        "morning": ["confirm or replan periods, tasks, decisions, and assignments"],
        "evening": outcomes or ["record completed, partial, blocked, and not-started work with reasons"],
        "acknowledgement_inferred": False,
        "end_check": {"requested": not known, "reason": "The result is not already known." if not known else "No end check: the result is already known."},
    }


def _standing_rule(request: dict[str, Any]) -> dict[str, Any]:
    """Render a proposal and never activate it."""

    value = request.get("standing_rule") or {}
    proposed = request.get("mode") == "standing_rule" or bool(value)
    return {
        "proposed": proposed,
        "activated": False,
        "trigger": str(value.get("trigger", "")),
        "automatic_action": str(value.get("automatic_action", "")),
        "exceptions": [str(item) for item in value.get("exceptions", [])],
        "affected_agents_or_systems": [str(item) for item in value.get("affected_agents_or_systems", [])],
        "permanence_or_review_date": str(value.get("permanence_or_review_date", "")),
    }


def _empty_result(request: dict[str, Any], *, status: str, mode: str, disposition: str) -> dict[str, Any]:
    """Build a complete redacted result for fail-closed paths."""

    return {
        "status": status, "mode": mode, "idempotency_key": _key(request), "items": [], "priority_order": [],
        "capacity_decision": _capacity(request.get("capacity") or {}), "flexible_period": _flexible_period(request.get("capacity") or {}),
        "reviews": _review(request), "monthly_report": {"included": mode == "monthly_report", "mobile_friendly": True, "contains_task_ids": False, "omits_minor_task_dump": True},
        "standing_rule": _standing_rule(request), "decisions": [{"matter": disposition, "recommendation": "Supply bounded evidence or consumer authority.", "reason": "The provider fails closed on material uncertainty.", "choices": ["Provide evidence", "Keep pending", "Other — specify"]}],
        "evidence_refs": [], "effects": dict(EFFECTS), "rollback": ROLLBACK_TARGET,
    }


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic time-management plan with no external effects."""

    if not isinstance(request, dict):
        raise ValueError("input must be an object")
    mode = str(request.get("mode", "intake"))
    if PRIVATE_MARKER.search(json.dumps(request, sort_keys=True)) or request.get("privacy_classification") == "restricted":
        return _empty_result(request, status="FAILED", mode=mode, disposition="privacy_rejected")
    evidence = request.get("source_evidence")
    if not isinstance(evidence, list) or not evidence or any(not isinstance(item, dict) or not all(item.get(field) for field in ("ref", "status", "provenance", "licence")) for item in evidence):
        return _empty_result(request, status="FAILED", mode=mode, disposition="needs-evidence")
    refs = [str(item["ref"]) for item in evidence]
    if any(item.get("status") in {"unknown", "not_reported"} for item in evidence):
        result = _empty_result(request, status="PENDING_APPROVAL", mode=mode, disposition="needs-evidence")
        result["evidence_refs"] = refs
        return result
    actions = request.get("requested_actions") or ["prepare"]
    if any(action in {"schedule", "send", "commit", "activate"} for action in actions):
        result = _empty_result(request, status="PENDING_APPROVAL", mode=mode, disposition="authority_escalation")
        result["evidence_refs"] = refs
        return result
    capacity = request.get("capacity") or {}
    task_inputs = request.get("tasks") or []
    ordered = sorted(enumerate(task_inputs), key=lambda pair: (_priority(pair[1]), pair[0]))
    used: set[str] = set()
    items: list[dict[str, Any]] = []
    for rank, (index, task) in enumerate(ordered, start=1):
        if not isinstance(task, dict):
            continue
        task_id = _task_id(task, index)
        confirmation = str(task.get("confirmation", "Provisional"))
        status = str(task.get("status", "Ready"))
        if status not in STATUSES:
            status = "Provisional"
        verification = ""
        evidence_required = [str(item) for item in task.get("evidence_refs", [])]
        if status == "Verified complete" and (str(task.get("owner")) in {"Lisa", "subordinate"} and not task.get("verification_ref")):
            status = "Awaiting agent evidence"
            verification = "Required verification receipt is missing."
            evidence_required.append("verification receipt")
        elif status == "Completed — Carlos reported":
            verification = "Accepted as Principal-reported completion."
        elif status == "Verified complete":
            verification = "Consumer supplied verification receipt present."
        period = _proposed_period(task, list(capacity.get("periods") or []), used) if status not in {"Cancelled", "duplicate", "created by mistake"} else None
        items.append({"task_id": task_id, "title": str(task.get("title", "")), "confirmation": confirmation, "owner": str(task.get("owner", "unassigned")), "status": status, "priority_rank": rank, "estimated_periods": int(task.get("estimated_periods", 1)), "dependencies": [str(item) for item in task.get("dependencies", [])], "unlocks": [str(item) for item in task.get("unlocks", [])], "external_mappings": {str(key): str(value) for key, value in (task.get("external_mappings") or {}).items()}, "proposed_period": period, "evidence_required": evidence_required, "verification": verification})
    priority_order = [item["task_id"] for item in items]
    pending = any(item["confirmation"] == "Provisional" or item["status"] == "Awaiting agent evidence" for item in items)
    if capacity.get("state") in {"reduced", "unavailable"}:
        pending = True
    result = {
        "status": "PENDING_APPROVAL" if pending else "COMPLETED", "mode": mode, "idempotency_key": _key(request), "items": items, "priority_order": priority_order,
        "capacity_decision": _capacity(capacity), "flexible_period": _flexible_period(capacity), "reviews": _review(request),
        "monthly_report": {"included": mode == "monthly_report", "mobile_friendly": True, "contains_task_ids": bool(items), "omits_minor_task_dump": True},
        "standing_rule": _standing_rule(request),
        "decisions": [{"matter": "material planning authority", "recommendation": "Keep external writes with the consumer owner.", "reason": "LiNKskills is not an authorization plane.", "choices": ["Prepare only", "Request owner approval", "Other — specify"]}],
        "evidence_refs": refs, "effects": dict(EFFECTS), "rollback": ROLLBACK_TARGET,
    }
    return result


def main() -> int:
    """Read one JSON request from stdin and emit one JSON result."""

    try:
        value = json.load(sys.stdin)
        print(json.dumps(normalize_request(value), sort_keys=True))
        return 0
    except Exception as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
