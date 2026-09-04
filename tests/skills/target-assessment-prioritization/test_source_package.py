from __future__ import annotations
import hashlib, importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SKILL_ID=Path(__file__).resolve().parents[0].name
SKILL=ROOT/'skills'/SKILL_ID
EVIDENCE=ROOT/'evidence'/'certification'/SKILL_ID/'source-package-evidence.json'
spec=importlib.util.spec_from_file_location(f'{SKILL_ID}_helper',SKILL/'scripts'/'helper_tool.py'); HELPER=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(HELPER)
def suite(): return json.loads((SKILL/'references'/'eval-suite.json').read_text())
def fixture(case_id='ordinary-ready'):
 return next(x for x in suite()['cases'] if x['case_id']==case_id)['contextual_inputs']['input_fixture']
class SourcePackageTests(unittest.TestCase):
 def test_positive_schema_instance_and_exact_output(self):
  case=next(x for x in suite()['cases'] if x['case_id']=='ordinary-ready'); output=HELPER.evaluate(case['contextual_inputs']['input_fixture'])
  self.assertEqual(output,case['contextual_inputs']['expected_output']); self.assertFalse(any(output['effects'].values())); self.assertFalse(output['selectable'])
 def test_prohibited_sensitive_mutating_and_authority_actions_block(self):
  for action in ('select','activate','contact','publish','certify','mutate_linktarget','claim_program_authority','claim_live_platform_use','infer_sensitive_traits'):
   payload=fixture(); payload['requested_action']=action; output=HELPER.evaluate(payload)
   self.assertEqual(output['status'],'BLOCKED',action); self.assertEqual(output['items'],[]); self.assertFalse(any(output['effects'].values())); self.assertFalse(output['program_authority']); self.assertFalse(output['live_platform_use'])
 def test_cross_reference_integrity_rejects_unknown_criterion_and_evidence(self):
  bad=fixture(); bad['items'][0]['criterion_results'][0]['criterion_id']='criterion:missing'
  with self.assertRaisesRegex(ValueError,'undeclared criterion reference'): HELPER.evaluate(bad)
  bad=fixture(); bad['items'][0]['evidence_refs']=['fixture:missing']
  with self.assertRaisesRegex(ValueError,'undeclared evidence reference'): HELPER.evaluate(bad)
 def test_schema_rejects_nonempty_effects_and_authority_claims(self):
  schema=HELPER.load('schemas.json'); output=HELPER.evaluate(fixture())
  for key,value in [('selectable',True),('program_authority',True),('live_platform_use',True)]:
   bad=json.loads(json.dumps(output)); bad[key]=value; result=HELPER.validate_instance(bad,{'$ref':'#/definitions/output','definitions':schema['definitions']}); self.assertFalse(result.ok,key)
  bad=json.loads(json.dumps(output)); bad['effects']['mutations']=['LiNKtarget.write']; result=HELPER.validate_instance(bad,{'$ref':'#/definitions/output','definitions':schema['definitions']}); self.assertFalse(result.ok)
 def test_runner_binding_and_retained_results_are_source_validation_only(self):
  result=HELPER.run_suite(); retained=json.loads((SKILL/'references'/'eval-results.json').read_text()); self.assertEqual(result,retained); self.assertTrue(result['passed']); self.assertEqual(result['evidence_kind'],'source_validation_only'); self.assertEqual(result['certification_status'],'uncertified'); self.assertEqual(result['publication_status'],'not_published'); self.assertFalse(result['linktarget_mutated'])
 def test_local_source_provenance_digests_and_mapping(self):
  provenance=json.loads((SKILL/'references'/'source-provenance.json').read_text()); self.assertEqual(provenance['work_package'],'LT-WP-007'); self.assertEqual(provenance['classification'],'source_validation_only')
  ids={x['source_id'] for x in provenance['methodology_sources']}; mapped=set(provenance['mapping'][0]['source_ids']); self.assertEqual(ids,mapped)
  for source in provenance['methodology_sources']:
   self.assertEqual(source['digest'],'sha256:'+hashlib.sha256((ROOT/source['source_id']).read_bytes()).hexdigest()); self.assertTrue(source['version'])
 def test_package_and_evidence_remain_globally_ineligible(self):
  text=(SKILL/'SKILL.md').read_text(); self.assertIn('globally ineligible and non-selectable',text)
  evidence=json.loads(EVIDENCE.read_text()); self.assertEqual(evidence['certification_status'],'uncertified'); self.assertEqual(evidence['publication_status'],'not_published'); self.assertFalse(evidence['selectable']); self.assertFalse(evidence['program_authority']); self.assertFalse(evidence['live_platform_use']); self.assertFalse(evidence['linktarget_mutated'])
  actual={x.relative_to(SKILL).as_posix():'sha256:'+hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(SKILL.rglob('*')) if x.is_file() and '__pycache__' not in x.parts}; self.assertEqual(actual,evidence['artifact_hashes'])
if __name__=='__main__': unittest.main()
