import unittest
from linkskills_persistence import MemoryStore
class MemoryStoreTests(unittest.TestCase):
 def test_isolation_and_privacy(self):
  s=MemoryStore(); s.put_release('a','r',{'x':1})
  with self.assertRaises(ValueError): s.get_release('b','r')
  s.reject(b'secret', 'prohibited'); self.assertNotIn('secret',str(s.rejections[0]))
 def test_idempotency_and_cas(self):
  s=MemoryStore(); self.assertEqual(s.receipt('a','k','d'),s.receipt('a','k','d')); s.cas_current('a','x',None,'1')
 def test_platform_apply_receipt_is_idempotent_and_collection_bound(self):
  s=MemoryStore()
  s.vendor_releases[('org','release-1')]={'collection_id':'collection-a'}
  receipt={'receipt_id':'apply-1','authority':'LiNKplatform','operation':'apply','applied':True}
  s.apply_platform_receipt('org','collection-a','release-1',expected_current=None,receipt=receipt)
  history_size=len(s.pointer_history)
  replay=s.apply_platform_receipt('org','collection-a','release-1',expected_current='release-1',receipt=receipt)
  self.assertEqual(replay['receipt_id'],'apply-1'); self.assertEqual(len(s.pointer_history),history_size)
  with self.assertRaisesRegex(ValueError,'apply_receipt_operation_invalid'):
   s.apply_platform_receipt('org','collection-a','release-1',expected_current='release-1',receipt={**receipt,'receipt_id':'rollback-1','operation':'rollback'})
  with self.assertRaisesRegex(ValueError,'apply_release_collection_mismatch'):
   s.apply_platform_receipt('org','collection-b','release-1',expected_current=None,receipt={**receipt,'receipt_id':'apply-2'})
