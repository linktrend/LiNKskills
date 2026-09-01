#!/usr/bin/env python3
"""Deterministic source-only target methodology evaluator."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "contracts"))
from linkskills_contracts.validate import validate_instance
ROOT=Path(__file__).resolve().parents[1]
EMPTY={"messages_sent":[],"external_calls":[],"selections":[],"mutations":[]}
PROHIBITED={"record","select","activate","contact","publish","certify","mutate_linktarget","claim_program_authority","claim_live_platform_use","infer_sensitive_traits"}
def load(name: str)->dict[str,Any]: return json.loads((ROOT/'references'/name).read_text())
def validate_refs(payload:dict[str,Any])->None:
 evidence={x['ref'] for x in payload['source_evidence']}; criteria={x['criterion_id'] for x in payload['criteria']}
 for criterion in payload['criteria']:
  if criterion['evidence_ref'] not in evidence: raise ValueError(f"undeclared evidence reference: {criterion['evidence_ref']}")
 for item in payload['items']:
  for ref in item['evidence_refs']:
   if ref not in evidence: raise ValueError(f"undeclared evidence reference: {ref}")
  for result in item['criterion_results']:
   if result['criterion_id'] not in criteria: raise ValueError(f"undeclared criterion reference: {result['criterion_id']}")
def evaluate(payload:dict[str,Any])->dict[str,Any]:
 schema=load('schemas.json'); errors = validate_instance(payload, {'$ref':'#/definitions/input','definitions':schema['definitions']})
 if not errors.ok: raise ValueError('input schema: ' + '; '.join(str(x) for x in errors.errors))
 validate_refs(payload)
 action=payload['requested_action']; blocked=action in PROHIBITED
 unknown=any(x['result']=='unknown' for item in payload['items'] for x in item['criterion_results']) or any(x['status']=='not_reported' for x in payload['source_evidence'])
 output={"status":"BLOCKED" if blocked else "DRAFT" if unknown else "READY_FOR_OWNER","matter_ref":payload['matter_ref'],"items":[] if blocked else sorted(payload['items'],key=lambda x:x['item_ref']),"uncertainty":[f"prohibited_action:{action}"] if blocked else (["incomplete_evidence"] if unknown else []),"effects":dict(EMPTY),"lifecycle_state":"draft","certification_state":"uncertified","publication_status":"not_published","selectable":False,"program_authority":False,"live_platform_use":False}
 errors = validate_instance(output, {'$ref':'#/definitions/output','definitions':schema['definitions']})
 if not errors.ok: raise ValueError('output schema: ' + '; '.join(str(x) for x in errors.errors))
 if any(output['effects'].values()): raise ValueError('effects must be empty')
 return output
def run_suite()->dict[str,Any]:
 suite=load('eval-suite.json'); results=[]
 for case in suite['cases']:
  try:
   fixture=case['contextual_inputs']['input_fixture']; output=evaluate(fixture)
   passed='expected_output' in case['contextual_inputs'] and output==case['contextual_inputs']['expected_output']; detail='exact_output' if passed else 'unexpected output'
  except Exception as exc:
   output=None; passed=case['contextual_inputs'].get('expected_error')==str(exc); detail=str(exc)
  results.append({'case_id':case['case_id'],'passed':passed,'assertions':case['expected']['criteria'],'detail':detail,'fixture_digest':'sha256:'+hashlib.sha256(json.dumps(case['contextual_inputs']['input_fixture'],sort_keys=True,separators=(',',':')).encode()).hexdigest()})
 result={'evidence_kind':'source_validation_only','skill_id':suite['skill_id'],'suite_version':suite['suite_version'],'passed':all(x['passed'] for x in results),'certification_status':'uncertified','publication_status':'not_published','selectable':False,'program_authority':False,'live_platform_use':False,'linktarget_mutated':False,'results':results}
 return result
def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--run-suite',action='store_true'); ap.add_argument('--input',type=Path); ap.add_argument('--results',type=Path); args=ap.parse_args()
 try:
  result=run_suite() if args.run_suite else evaluate(json.loads((args.input.read_text() if args.input else sys.stdin.read())))
  rendered=json.dumps(result,indent=2,sort_keys=True)+'\n'
  if args.results: args.results.write_text(rendered)
  sys.stdout.write(rendered); return 0 if result.get('passed',True) else 1
 except Exception as exc: print(json.dumps({'status':'error','message':str(exc)},sort_keys=True),file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
