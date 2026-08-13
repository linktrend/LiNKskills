import unittest
from linkskills_core.release_v2 import ReleaseError, inventory_digest
class ReleaseV2(unittest.TestCase):
 def test_inventory_is_deterministic_and_safe(self):
  self.assertEqual(inventory_digest({'a.txt':b'a','b.txt':b'b'}), inventory_digest({'b.txt':b'b','a.txt':b'a'}))
  with self.assertRaises(ReleaseError): inventory_digest({'../bad':b'x'})
