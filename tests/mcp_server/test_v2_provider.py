import unittest
from linkskills_mcp.v2_provider import V2Provider, RESOURCE_OPERATIONS, TOOLS
class V2ProviderTests(unittest.TestCase):
 def setUp(self): self.p=V2Provider(); self.base={'protocol_version':'2026-07-28','authorization':'bound','version':'1.0.0'}
 def test_resource_first_tools_restricted(self):
  self.assertEqual(len(self.p.resources()),13); self.assertEqual(len(self.p.tools()),6); self.assertTrue(set(RESOURCE_OPERATIONS).isdisjoint(TOOLS))
 def test_session_downgrade_and_execution_fail_closed(self):
  for r,e in [({'operation':'initialize'},'session_not_supported'),({'operation':'skills_run_start'},'legacy_execution_disabled'),({'operation':'skills_list','protocol_version':'2024-11-05'},'contract_incompatible')]:
   x=dict(self.base,**r); self.assertEqual(self.p.handle(x)['error'],e)
 def test_exact_resource_bounded(self):
  x=self.p.handle(dict(self.base,operation='skills_release_describe',limit=2)); self.assertTrue(x['ok']); self.assertTrue(x['no_fallback'])
  self.assertEqual(self.p.handle(dict(self.base,operation='skills_release_describe',version=''))['error'],'exact_release_required')
