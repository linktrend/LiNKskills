import unittest
from linkskills_gateway.capability_status_v2 import CapabilityStatus, readiness
class CapabilityStatusTests(unittest.TestCase):
 def test_readiness_is_truthful(self):
  a=CapabilityStatus('catalogue_index','available'); b=CapabilityStatus('qualification_evaluation','offline')
  r=readiness([a,b]); self.assertEqual(r['readiness'],'not_ready'); self.assertIn('qualification_evaluation',r['blocked_capabilities'])
 def test_reject_invalid_state(self):
  with self.assertRaises(ValueError): CapabilityStatus('catalogue_index','healthy')
