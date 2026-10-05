#!/usr/bin/env python3
"""Run the deterministic capacity helper and validate its actual result."""
import argparse
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from helper_tool import normalize_request

SKILL_ROOT=Path(__file__).resolve().parents[1]
FIXTURE_PATH=SKILL_ROOT/"references/capacity-review-eval-fixtures.json"
SCHEMA_PATH=SKILL_ROOT/"references/schemas.json"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--case",required=True)
    args=parser.parse_args()
    try:
        cases=json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]
        case=next(c for c in cases if c["case_id"]==args.case)
        schemas=json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        defs=schemas["definitions"]
        input_schema={"$schema":"https://json-schema.org/draft/2020-12/schema","$ref":"#/definitions/input","definitions":defs}
        output_schema={"$schema":"https://json-schema.org/draft/2020-12/schema","$ref":"#/definitions/output","definitions":defs}
        Draft202012Validator.check_schema(input_schema)
        Draft202012Validator.check_schema(output_schema)
        findings=[]
        input_errors=list(Draft202012Validator(input_schema,format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(case["input"]))
        expected_input_valid=case.get("expected_input_schema_valid",True)
        if bool(input_errors)!= (not expected_input_valid): findings.append("input_schema_validity_mismatch")
        actual=normalize_request(case["input"])
        for err in Draft202012Validator(output_schema,format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(actual):
            findings.append("output_schema_invalid")
        if actual.get("status")!=case["expected_helper_status"]:
            findings.append("helper_status_mismatch")
        for key in ("mode","plan_ref","horizon","period"):
            if actual.get(key)!=case["input"].get(key): findings.append(key+"_identity_mismatch")
        expected_evidence=[x["ref"] for x in case["input"]["source_evidence"]]
        if actual.get("evidence")!=expected_evidence: findings.append("source_evidence_identity_mismatch")
        expected_objectives=[]
        for obj in case["input"]["objectives"]:
            expected_objectives.append({"id":obj["id"],"statement":obj["statement"],"owner_ref":obj["owner_ref"],"evidence_ref":obj["evidence_ref"]})
        if case["expected_helper_status"]!="BLOCKED" and actual.get("objectives")!=expected_objectives: findings.append("objective_identity_or_owner_mismatch")
        expected=case["expected_capacity_row"]
        rows=actual.get("capacity_review")
        if expected is None:
            if rows is not None: findings.append("invalid_input_returned_capacity_rows")
        elif not isinstance(rows,list) or len(rows)!=1:
            findings.append("capacity_row_missing_or_extra")
        else:
            row=rows[0]; unit=case["input"]["capacity_units"][0]
            for key,value in expected.items():
                if row.get(key)!=value: findings.append("capacity_"+key+"_mismatch")
            for key in ("unit_ref","role","period","time_unit"):
                if row.get(key)!=unit.get(key): findings.append("capacity_"+key+"_identity_mismatch")
            supplied=sorted({q["evidence_ref"] for name,q in unit.items() if name in {"gross_available","planned_unavailable","recurring_load","existing_commitments","proposed_demand"} and q["value"] is not None})
            if row.get("evidence_refs")!=supplied: findings.append("capacity_evidence_identity_mismatch")
        if actual.get("effects")!={"messages_sent":[],"external_calls":[],"mutations":[]}:
            findings.append("effects_not_empty")
        if actual.get("ownership")!={"mutable_state_created":False,"duplicate_state_created":False}:
            findings.append("ownership_boundary_mismatch")
        findings=sorted(set(findings))
        print(json.dumps({"case_id":args.case,"status":"PASS" if not findings else "FAIL","checked_actual_helper_result":True,"schema":"Draft202012Validator","finding_codes":findings},sort_keys=True))
        return 0 if not findings else 1
    except (OSError,KeyError,StopIteration,TypeError,ValueError,json.JSONDecodeError):
        print(json.dumps({"case_id":args.case,"status":"ERROR","checked_actual_helper_result":False,"finding_codes":["fixture_helper_or_schema_error"]},sort_keys=True))
        return 2

if __name__=="__main__": raise SystemExit(main())
