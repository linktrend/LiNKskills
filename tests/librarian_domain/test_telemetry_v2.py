import unittest
from linkskills_librarian.telemetry_v2 import TelemetryPort
class TelemetryV2(unittest.TestCase):
 def report(self): return {'report_kind':'completed_use','score':9,'issue':{'type':'incorrect'},'idempotency_key':'a','skill_release_ref':'r','consumer_class':'codex','actor_class':'agent_actor','runtime_profile_ref':'p'}
 def test_idempotency_and_privacy(self):
  p=TelemetryPort(); first=p.submit(self.report()); self.assertEqual(first,p.submit(self.report()))
  bad=self.report(); bad['prompt']='x'; self.assertFalse(p.submit(bad)['accepted']); self.assertNotIn('prompt',p.submit(bad))
 def test_aggregation(self): self.assertEqual(sum(TelemetryPort().aggregate().values()),0)
