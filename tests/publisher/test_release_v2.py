import unittest
from linkskills_publisher.release_v2 import ReleaseRegistry, PublisherAttestation
from linkskills_core.release_v2 import ReleaseError
class PublisherV2(unittest.TestCase):
 def test_exact_cas_and_verify(self):
  r=ReleaseRegistry(); r.publish('a','1.0.0',{'README.md':b'x'}); r.set_current('a','1.0.0',None)
  self.assertEqual(r.verify('a','1.0.0',{'README.md':b'x'}),'verified')
  with self.assertRaises(ReleaseError): r.exact('a','latest')
 def test_attestation_fixed_algorithm(self):
  with self.assertRaises(ReleaseError): PublisherAttestation('RS256','k','o','a','p').verify_metadata(organization='o',audience='a',capability='p')
