#!/usr/bin/env python3
"""Helper utility for workflow-architect skill."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator
from typing import Any


def _normalize_process_review(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize an evidenced process map; never create or execute a workflow."""
    required=("process_ref","objective","scope","as_of","source_evidence","known_owner_refs","current_steps","controls","exceptions","measures")
    if any(key not in payload for key in required):
        raise ValueError("process_review requires its separate complete contract")
    definitions=json.loads((Path(__file__).resolve().parents[1]/"references/schemas.json").read_text())["definitions"]
    schema={"$ref":"#/definitions/process_review_input","definitions":definitions}
    if list(Draft202012Validator(schema,format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(payload)):
        raise ValueError("invalid process_review input contract")
    evidence=payload["source_evidence"]
    if not isinstance(evidence,list): raise ValueError("source_evidence must be an array")
    by_ref={}
    for item in evidence:
        if not isinstance(item,dict) or item.get("status") not in {"observed","reported","not_reported"} or not isinstance(item.get("ref"),str): raise ValueError("invalid process evidence record")
        if item["ref"] in by_ref: raise ValueError("duplicate process evidence reference")
        by_ref[item["ref"]]=item
    refs=set(by_ref)
    arrays=("current_steps","controls","exceptions","measures")
    for key in arrays:
        if not isinstance(payload[key],list): raise ValueError(f"{key} must be an array")
    def check_refs(row, fields):
        for field in fields:
            values=row.get(field,[])
            if not isinstance(values,list) or any(value not in refs for value in values): raise ValueError(f"{field} must use supplied evidence refs")
    steps=[]; gaps=[]; questions=[]
    seen=set()
    for row in payload["current_steps"]:
        if not isinstance(row,dict) or not isinstance(row.get("step_ref"),str) or row["step_ref"] in seen: raise ValueError("current step refs must be unique")
        seen.add(row["step_ref"]); check_refs(row,("evidence_refs",))
        statuses=[by_ref[r]["status"] for r in row.get("evidence_refs",[])]
        src_status="observed" if "observed" in statuses else ("reported" if "reported" in statuses else "not_reported")
        steps.append({**row,"source_status":src_status})
        if row.get("actor_ref") is None:
            gaps.append({"subject_ref":row["step_ref"],"field":"actor_ref","status":"not_reported","reason":"No owner/actor reference supplied for this current step."})
            questions.append(f"Who owns current step {row['step_ref']}?")
    controls=[]; seen=set()
    for row in payload["controls"]:
        if not isinstance(row,dict) or not isinstance(row.get("control_ref"),str) or row["control_ref"] in seen: raise ValueError("control refs must be unique")
        seen.add(row["control_ref"]); check_refs(row,("evidence_refs",)); controls.append(dict(row))
        if row.get("owner_ref") is None:
            gaps.append({"subject_ref":row["control_ref"],"field":"owner_ref","status":"not_reported","reason":"Control owner was not supplied; preserve the control and request owner review."})
            questions.append(f"Who owns control {row['control_ref']}?")
    exceptions=[]; seen=set()
    for row in payload["exceptions"]:
        if not isinstance(row,dict) or not isinstance(row.get("exception_ref"),str) or row["exception_ref"] in seen: raise ValueError("exception refs must be unique")
        seen.add(row["exception_ref"]); check_refs(row,("evidence_refs",)); exceptions.append(dict(row))
        for field in ("owner_ref", "disposition"):
            if row.get(field) is None:
                gaps.append({"subject_ref":row["exception_ref"],"field":field,"status":"not_reported","reason":"Exception handling detail not supplied; request owner review."})
                questions.append(f"Who confirms {field} for exception {row['exception_ref']}?")
    if not exceptions:
        gaps.append({"subject_ref":payload["process_ref"],"field":"exceptions","status":"not_reported","reason":"No exception path was supplied; this does not mean none exist."})
        questions.append("What exceptions, escalations, and alternate paths must the process handle?")
    measures=[]; seen=set()
    for row in payload["measures"]:
        if not isinstance(row,dict) or not isinstance(row.get("metric_ref"),str) or row["metric_ref"] in seen: raise ValueError("metric refs must be unique")
        seen.add(row["metric_ref"])
        ref=row.get("evidence_ref")
        if ref is not None and ref not in refs: raise ValueError("measure evidence_ref must be supplied")
        if row.get("value") is not None and (ref is None or not row.get("unit") or not row.get("period")): raise ValueError("measured value requires supplied evidence, unit, and period")
        measures.append(dict(row))
        if row.get("value") is None:
            gaps.append({"subject_ref":row["metric_ref"],"field":"value","status":"not_reported","reason":"No measured value was supplied; retain null."})
            questions.append(f"Is there a measured baseline for {row['name']} with period and unit?")
    if not isinstance(payload["known_owner_refs"],list): raise ValueError("known_owner_refs must be an array")
    return {"mode":"process_review","status":"NEEDS_OWNER_REVIEW" if gaps else "DRAFT","process_ref":payload["process_ref"],"objective":payload["objective"],"scope":payload["scope"],"as_of":payload["as_of"],"source_evidence":evidence,"current_steps":steps,"controls":controls,"exceptions":exceptions,"measures":measures,"gaps":gaps,"pain_points":[],"impact_claims":[],"future_state_draft":[],"owner_questions":questions,"effects":{}}


def normalize_requirement(raw_json: str) -> dict[str, Any]:
    payload = json.loads(raw_json)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    if payload.get("mode") == "process_review":
        return _normalize_process_review(payload)
    normalized = {
        "agent_id": str(payload.get("agent_id", "")).strip(),
        "project_id": str(payload.get("project_id", "")).strip(),
        "workflow_name": str(payload.get("workflow_name", "")).strip(),
        "objective": str(payload.get("objective", "")).strip(),
        "trigger_type": str(payload.get("trigger_type", "manual")).strip(),
        "test_payload": payload.get("test_payload", {}),
    }
    return normalized


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: helper_tool.py '<json_payload>'")
        raise SystemExit(1)
    result = normalize_requirement(sys.argv[1])
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
