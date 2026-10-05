#!/usr/bin/env python3
"""Check an actual organizational evidence-map response against its request."""
import argparse, json, sys
from datetime import date, datetime
from pathlib import Path
import jsonschema

def evaluate(request, response):
    f=[]
    schema=json.loads((Path(__file__).resolve().parents[1]/"references/schemas.json").read_text())
    for value, name in ((request,"organizational_evidence_map_input"),(response,"organizational_evidence_map_output")):
        try:
            jsonschema.validate(value,{"$ref":"#/definitions/"+name,"definitions":schema["definitions"]},format_checker=jsonschema.FormatChecker())
        except jsonschema.ValidationError:
            f.append(name+"_schema_invalid")
    if f: return f
    identity=response["framework_identity"]
    jurisdiction=request["jurisdiction_or_unknown_reason"]
    framework=request["framework_name_and_version_or_unknown_reason"]
    for key, expected in (("as_of",request["as_of"]),("jurisdiction",jurisdiction.get("jurisdiction")),("framework_name",framework.get("framework_name")),("version",framework.get("version"))):
        if identity.get(key)!=expected: f.append("framework_"+key+"_not_preserved")
    reasons=list(dict.fromkeys(x["unknown_reason"] for x in (jurisdiction,framework) if "unknown_reason" in x))
    expected_reason="; ".join(reasons) if reasons else None
    if identity.get("unknown_reason")!=expected_reason: f.append("framework_unknown_reason_not_preserved")
    if request.get("mode")!="organizational_evidence_map" or response.get("mode")!="organizational_evidence_map": f.append("mode_mismatch")
    if response.get("status") not in {"DRAFT","READY_FOR_OWNER","NEEDS_CONTEXT"}: f.append("invalid_status")
    if response.get("scope_ref")!=request.get("scope_ref"): f.append("scope_not_preserved")
    if response.get("effects")!={} or response.get("qualification_claim") is not False: f.append("effects_or_qualification_claim")
    if any(k in response for k in ("platform_verdict","compliance_verdict","legal_conclusion","certification")): f.append("legacy_or_authority_field")
    sources=request.get("requirement_source_refs"); rows=response.get("requirements")
    if not isinstance(sources,list) or not isinstance(rows,list): return f+["requirements_not_arrays"]
    byid={x.get("requirement_id"):x for x in sources if isinstance(x,dict)}; out={x.get("id"):x for x in rows if isinstance(x,dict)}
    if len(byid)!=len(sources) or len(out)!=len(rows) or set(out)!=set(byid): f.append("requirement_ids_missing_extra_or_duplicate")
    controls=request.get("supplied_controls_and_evidence_refs",[])
    if not isinstance(controls,list): controls=[]; f.append("controls_not_array")
    for rid,row in out.items():
        src=byid.get(rid)
        if src and row.get("source_ref")!=src.get("source_ref"): f.append("requirement_source_not_preserved")
        cref=row.get("control_ref")
        if cref is None:
            if row.get("control_owner_ref") is not None or row.get("evidence_refs")!=[] or row.get("last_verified_at") is not None: f.append("unmapped_requirement_has_control_facts")
            if row.get("status")=="evidenced": f.append("unmapped_requirement_marked_evidenced")
            continue
        matched=[c for c in controls if isinstance(c,dict) and c.get("control_ref")==cref and rid in c.get("supports_requirement_ids",[])]
        if len(matched)!=1: f.append("control_mapping_not_supplied_for_requirement"); continue
        c=matched[0]
        if row.get("control_owner_ref")!=c.get("control_owner_ref"): f.append("control_owner_not_preserved")
        ev=row.get("evidence_refs"); allowed=c.get("evidence_refs",[])
        if not isinstance(ev,list) or len(ev)!=len(set(ev)) or set(ev)!=set(allowed): f.append("evidence_reference_not_supplied")
        verified=c.get("last_verified_at")
        if row.get("last_verified_at")!=verified: f.append("verification_time_not_supplied")
        if row.get("status")=="evidenced" and (not ev or not verified): f.append("evidenced_without_dated_evidence")
        if verified:
            try:
                if datetime.fromisoformat(verified.replace("Z","+00:00")).date()>date.fromisoformat(request["as_of"]): f.append("verification_after_as_of")
            except (KeyError,TypeError,ValueError): f.append("invalid_verification_date")
    if not sources and (response.get("status")!="NEEDS_CONTEXT" or rows): f.append("missing_source_must_need_context")
    return sorted(set(f))

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True,type=Path); p.add_argument("--output",required=True,type=Path); a=p.parse_args()
    try: req=json.loads(a.input.read_text()); out=json.loads(a.output.read_text()); findings=evaluate(req,out); print(json.dumps({"checked_actual_response":True,"passed":not findings,"finding_codes":findings},sort_keys=True)); return 0 if not findings else 1
    except (OSError,json.JSONDecodeError,TypeError): print(json.dumps({"checked_actual_response":False,"passed":False,"finding_codes":["input_or_output_unreadable"]},sort_keys=True)); return 2
if __name__=="__main__": raise SystemExit(main())
