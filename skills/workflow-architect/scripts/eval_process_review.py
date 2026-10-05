#!/usr/bin/env python3
"""Validate an actual process-review response against request and schemas."""
import argparse, json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
def evaluate(request,response):
    schemas=json.loads((ROOT/"references/schemas.json").read_text(encoding="utf-8")); defs=schemas["definitions"]
    inp={"$schema":"https://json-schema.org/draft/2020-12/schema","$ref":"#/definitions/process_review_input","definitions":defs}
    out={"$schema":"https://json-schema.org/draft/2020-12/schema","$ref":"#/definitions/process_review_output","definitions":defs}
    Draft202012Validator.check_schema(inp); Draft202012Validator.check_schema(out)
    f=[]
    if list(Draft202012Validator(inp,format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(request)): f.append("input_schema_invalid")
    if list(Draft202012Validator(out,format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(response)): f.append("output_schema_invalid")
    if f:
        return sorted(set(f))
    for key in ("mode","process_ref","objective","scope","as_of"):
        if response.get(key)!=request.get(key): f.append(key+"_identity_mismatch")
    if response.get("mode")!="process_review" or response.get("effects")!={}: f.append("mode_or_effect_boundary")
    if response.get("gaps") and response.get("status")!="NEEDS_OWNER_REVIEW": f.append("gaps_without_owner_review_status")
    if not response.get("gaps") and response.get("status")=="NEEDS_OWNER_REVIEW": f.append("owner_review_status_without_gap")
    if any(key in response for key in ("workflow_id","activated","tested","execution_id")): f.append("workflow_execution_field_present")
    source={x["ref"]:x for x in request.get("source_evidence",[]) if isinstance(x,dict) and isinstance(x.get("ref"),str)}
    if response.get("source_evidence")!=request.get("source_evidence"): f.append("source_evidence_not_preserved")
    def same_rows(input_key,output_key,id_key,extra=None):
        incoming=request.get(input_key,[]); returned=response.get(output_key,[])
        a={x.get(id_key):x for x in incoming if isinstance(x,dict)}; b={x.get(id_key):x for x in returned if isinstance(x,dict)}
        if len(a)!=len(incoming) or len(b)!=len(returned) or set(a)!=set(b): f.append(input_key+"_identity_missing_extra_or_duplicate"); return
        for rid,row in a.items():
            got=b[rid]
            for k,v in row.items():
                if k=="source_status": continue
                if got.get(k)!=v: f.append(input_key+"_field_not_preserved")
            if extra and not extra(row,got): f.append(input_key+"_evidence_or_owner_mismatch")
    def step_extra(row,got):
        statuses=[source[x]["status"] for x in row.get("evidence_refs",[]) if x in source]
        status="observed" if "observed" in statuses else ("reported" if "reported" in statuses else "not_reported")
        return got.get("source_status")==status
    same_rows("current_steps","current_steps","step_ref",step_extra)
    same_rows("controls","controls","control_ref")
    same_rows("exceptions","exceptions","exception_ref")
    same_rows("measures","measures","metric_ref")
    # Missing source facts require traceable gaps/questions, not a self-reported status.
    expected_gaps=set(); question_terms=[]
    for key,id_key,fields in (("current_steps","step_ref",("actor_ref",)),("controls","control_ref",("owner_ref",)),("exceptions","exception_ref",("owner_ref","disposition")),("measures","metric_ref",("value",))):
        for row in request[key]:
            for field in fields:
                if row[field] is None:
                    expected_gaps.add((row[id_key],field,"not_reported"))
                    question_terms.append(row["name"] if key=="measures" else row[id_key])
    if not request["exceptions"]:
        expected_gaps.add((request["process_ref"],"exceptions","not_reported"))
        question_terms.append("exceptions")
    actual_gaps={(row["subject_ref"],row["field"],row["status"]) for row in response["gaps"]}
    if not expected_gaps.issubset(actual_gaps): f.append("required_unknown_fact_gap_missing")
    questions=[text.strip().casefold() for text in response["owner_questions"] if text.strip().endswith("?")]
    if any(not any(term.casefold() in question for question in questions) for term in question_terms): f.append("required_unknown_fact_question_missing")
    required={x["control_ref"] for x in request.get("controls",[]) if x.get("required") is True}
    for key in ("current_steps","controls","exceptions"):
        for row in request[key]:
            if any(ref not in source for ref in row["evidence_refs"]): f.append("unsupplied_evidence_reference")
    for row in request["measures"]:
        if row["evidence_ref"] is not None and row["evidence_ref"] not in source: f.append("unsupplied_measure_evidence")
        if row["value"] is not None and (row["evidence_ref"] is None or not row["unit"] or not row["period"]): f.append("measurement_basis_missing")
    known=set(request.get("known_owner_refs",[]))
    for item in response.get("future_state_draft",[]):
        if not known and item.get("owner_ref") is not None: f.append("unsupported_future_owner")
        elif item.get("owner_ref") is not None and item.get("owner_ref") not in known: f.append("unsupported_future_owner")
        if not required.issubset(set(item.get("preserved_control_refs",[]))): f.append("required_approval_not_preserved")
        allowed=set(source)
        if any(ref not in allowed for ref in item.get("basis_refs",[])): f.append("future_basis_not_supplied")
    for claim in response.get("impact_claims",[]):
        if claim.get("claim_type")=="observed" and not claim.get("evidence_refs"): f.append("observed_impact_without_evidence")
        if any(ref not in source for ref in claim.get("evidence_refs",[])): f.append("impact_evidence_not_supplied")
    return sorted(set(f))

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True,type=Path); p.add_argument("--output",required=True,type=Path); a=p.parse_args()
    try:
        result=evaluate(json.loads(a.input.read_text(encoding="utf-8")),json.loads(a.output.read_text(encoding="utf-8")))
        print(json.dumps({"checked_actual_response":True,"status":"PASS" if not result else "FAIL","finding_codes":result},sort_keys=True)); return 0 if not result else 1
    except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError):
        print(json.dumps({"checked_actual_response":False,"status":"ERROR","finding_codes":["input_output_or_schema_error"]},sort_keys=True)); return 2
if __name__=="__main__": raise SystemExit(main())
