import unittest
from linkskills_eval_runner.sandbox_v2 import plan_candidate, qualification_outcome
class SandboxV2(unittest.TestCase):
 def test_attack_is_quarantined(self):
  with self.assertRaises(ValueError): plan_candidate({'declared_actions':['network'],'paths':['ok']})
 def test_workspace_is_deterministic_and_failure_holds(self):
  a=plan_candidate({'declared_actions':[],'paths':['a']}); b=plan_candidate({'declared_actions':[],'paths':['a']})
  self.assertEqual(a.workspace_id,b.workspace_id); self.assertEqual(qualification_outcome('escape'),'hold_quarantine')
