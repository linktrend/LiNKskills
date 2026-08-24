#!/usr/bin/env python3
"""Deterministic, offline PKT-18 meeting-management helper."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from typing import Any


ROLLBACK_TARGET = "ABSENT@517f22ee135c298a17a74f84a84b60accdf22cf4/tree:d2514ee298074c70f9bb5fb19f2fc71af7d43f16 (no prior qualified PKT-18 release)"
EFFECTS = {"external_calls": [], "messages_sent": [], "mutations": [], "private_state_writes": False}
PRIVATE_MARKER = re.compile(r"(?:sk_live|bearer\s+|password[\"']?\s*[:=]|access[_-]?token[\"']?\s*[:=]|api[_-]?key[\"']?\s*[:=]|private[_-]?key|BEGIN PRIVATE KEY|secret[\"']?\s*[:=]|raw[_-]?transcript|diagnosis[\"']?\s*[:=]|medical_record[\"']?\s*[:=]|customer@example\.com|/(?:Users|home|private/tmp)/)", re.IGNORECASE)


def _key(request: dict[str, Any]) -> str:
    """Return a stable request key without retaining input contents."""

    raw = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "mm-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _base(request: dict[str, Any], status: str, *, meeting_ref: str = "", disposition: str = "needs-evidence") -> dict[str, Any]:
    """Build a complete redacted output for fail-closed paths."""

    mode = str(request.get("mode", "full"))
    return {
        "status": status, "mode": mode, "idempotency_key": _key(request), "meeting_ref": meeting_ref,
        "agenda": {"objective": "", "items": [], "time_boxes": [], "evidence_prompts": [], "parking_lot": []},
        "prebrief": {"included": False, "private": True, "questions": [], "risk_prompts": [], "shared_routing_allowed": False},
        "notes": {"included": False, "summary": "", "evidence_refs": [], "raw_transcript_retained": False},
        "decisions": [], "follow_ups": [], "candidate_review": {"included": False, "disposition": "not_applicable", "reasons": [disposition], "schedule_mutated": False},
        "privacy": {"classification": str(request.get("privacy_classification", "unknown")), "raw_transcript_retained": False, "private_data_echoed": False},
        "effects": dict(EFFECTS), "rollback": ROLLBACK_TARGET,
    }


def _agenda(meeting: dict[str, Any]) -> dict[str, Any]:
    """Create a concise agenda from bounded fields."""

    items = [str(item) for item in meeting.get("agenda_items", [])]
    if not items:
        items = ["Confirm objective and desired decision", "Review evidence and dependencies", "Agree next steps and open questions"]
    return {"objective": str(meeting.get("purpose", "")), "items": items, "time_boxes": ["opening", *["discussion" for _ in items], "close"], "evidence_prompts": ["What supplied evidence supports this decision?", "What remains unknown or needs owner confirmation?"], "parking_lot": []}


def _prebrief(meeting: dict[str, Any]) -> dict[str, Any]:
    """Create private prompts which cannot be routed to shared notes."""

    desired = str(meeting.get("desired_decision", ""))
    questions = ["What decision is actually required?"]
    if desired:
        questions.append(f"What evidence would change the decision: {desired}")
    return {"included": True, "private": True, "questions": questions, "risk_prompts": ["Check unresolved authority, dependency, and evidence gaps."], "shared_routing_allowed": False}


def _decisions(meeting: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize supplied decisions without inventing them."""

    result = []
    for decision in meeting.get("decisions", []):
        if not isinstance(decision, dict):
            continue
        result.append({"decision_ref": str(decision.get("decision_ref", "")), "statement": str(decision.get("statement", "")), "owner": str(decision.get("owner", meeting.get("owner", ""))), "evidence_ref": str(decision.get("evidence_ref", "")), "confidence": str(decision.get("confidence", "unknown")), "alternatives": ["Proceed as supplied", "Keep pending", "Other — specify"]})
    return result


def _follow_ups(meeting: dict[str, Any]) -> list[dict[str, Any]]:
    """Require verification evidence for Verified follow-ups."""

    result = []
    for follow in meeting.get("follow_ups", []):
        if not isinstance(follow, dict):
            continue
        status = str(follow.get("status", "Proposed"))
        verification = ""
        if status == "Verified" and not follow.get("verification_ref"):
            status = "Awaiting evidence"
            verification = "Verification receipt is missing."
        elif status == "Verified":
            verification = "Consumer verification receipt supplied."
        else:
            verification = "No completion claim; retain the follow-up for consumer reconciliation."
        result.append({"follow_up_ref": str(follow.get("follow_up_ref", "")), "title": str(follow.get("title", "")), "owner": str(follow.get("owner", "")), "status": status, "deadline": str(follow.get("deadline", "")), "dependency": str(follow.get("dependency", "")), "destination_mappings": {str(k): str(v) for k, v in (follow.get("destination_mappings") or {}).items()}, "verification": verification})
    return result


def _candidate(meeting: dict[str, Any], mode: str) -> dict[str, Any]:
    """Recommend a candidate disposition without schedule mutation."""

    candidate = meeting.get("candidate") or {}
    if mode != "candidate_review" and not candidate:
        return {"included": False, "disposition": "not_applicable", "reasons": [], "schedule_mutated": False}
    reasons = []
    if candidate.get("duplicate_risk") is True:
        disposition = "review"
        reasons.append("possible duplicate meeting")
    elif not candidate.get("decision_value"):
        disposition = "review"
        reasons.append("decision value is not evidenced")
    else:
        disposition = "maintain"
        reasons.append("purpose and decision value supplied")
    return {"included": True, "disposition": disposition, "reasons": reasons, "schedule_mutated": False}


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, effect-free meeting-management result."""

    if not isinstance(request, dict):
        raise ValueError("input must be an object")
    meeting = request.get("meeting") if isinstance(request.get("meeting"), dict) else {}
    meeting_ref = str(meeting.get("meeting_ref", ""))
    mode = str(request.get("mode", "full"))
    serialized = json.dumps(request, sort_keys=True)
    if request.get("privacy_classification") == "restricted" or PRIVATE_MARKER.search(serialized) or "transcript_text" in request or "raw_transcript" in request:
        return _base(request, "FAILED", meeting_ref=meeting_ref, disposition="privacy_rejected")
    evidence = request.get("source_evidence")
    if not isinstance(evidence, list) or not evidence or any(not isinstance(item, dict) or not all(item.get(field) for field in ("ref", "status", "provenance", "licence")) for item in evidence):
        return _base(request, "FAILED", meeting_ref=meeting_ref, disposition="needs-evidence")
    refs = [str(item["ref"]) for item in evidence]
    if any(item.get("status") in {"unknown", "not_reported"} for item in evidence):
        result = _base(request, "PENDING_APPROVAL", meeting_ref=meeting_ref, disposition="needs-evidence")
        result["notes"]["evidence_refs"] = refs
        return result
    actions = request.get("requested_actions") or ["prepare"]
    if any(action in {"send", "create", "update", "retire", "reschedule"} for action in actions):
        return _base(request, "PENDING_APPROVAL", meeting_ref=meeting_ref, disposition="authority_escalation")
    if not meeting_ref or not meeting.get("purpose") or not meeting.get("owner"):
        return _base(request, "PENDING_APPROVAL", meeting_ref=meeting_ref, disposition="missing_meeting_identity")
    notes_text = str(meeting.get("redacted_notes", ""))
    result = {
        "status": "COMPLETED", "mode": mode, "idempotency_key": _key(request), "meeting_ref": meeting_ref,
        "agenda": _agenda(meeting), "prebrief": _prebrief(meeting),
        "notes": {"included": mode in {"notes", "full", "follow_up"} and bool(notes_text or meeting.get("transcript_ref")), "summary": notes_text[:1600], "evidence_refs": refs, "raw_transcript_retained": False},
        "decisions": _decisions(meeting), "follow_ups": _follow_ups(meeting), "candidate_review": _candidate(meeting, mode),
        "privacy": {"classification": str(request.get("privacy_classification")), "raw_transcript_retained": False, "private_data_echoed": False}, "effects": dict(EFFECTS), "rollback": ROLLBACK_TARGET,
    }
    if any(item["status"] == "Awaiting evidence" for item in result["follow_ups"]):
        result["status"] = "PENDING_APPROVAL"
    return result


def main() -> int:
    """Read one JSON request from stdin and emit one JSON result."""

    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            result = _base({}, "FAILED", disposition="invalid-input")
        else:
            result = normalize_request(payload)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] != "FAILED" else 1
    except Exception:
        # Preserve the complete fail-closed output contract without echoing
        # parser errors or malformed/private input.
        print(json.dumps(_base({}, "FAILED", disposition="invalid-input"), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
