import unittest
from linkskills_persistence import MemoryStore
class MemoryStoreTests(unittest.TestCase):
 def test_isolation_and_privacy(self):
  s=MemoryStore(); s.put_release('a','r',{'x':1})
  with self.assertRaises(ValueError): s.get_release('b','r')
  s.reject(b'secret', 'prohibited'); self.assertNotIn('secret',str(s.rejections[0]))
 def test_idempotency_and_cas(self):
  s=MemoryStore(); self.assertEqual(s.receipt('a','k','d'),s.receipt('a','k','d')); s.cas_current('a','x',None,'1')
