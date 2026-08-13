import unittest

from linkskills_core.release_v2 import ReleaseError
from linkskills_publisher.release_v2 import PublisherAttestation, ReleaseRegistry


class PublisherV2(unittest.TestCase):
    def test_exact_cas_and_verify(self):
        registry = ReleaseRegistry(); registry.publish("a", "1.0.0", {"README.md": b"x"}); registry.set_current("a", "1.0.0", None)
        self.assertEqual(registry.verify("a", "1.0.0", {"README.md": b"x"}), "verified")
        with self.assertRaises(ReleaseError): registry.exact("a", "latest")
        with self.assertRaises(ReleaseError): registry.set_current("a", "1.0.0", "wrong")

    def test_attestation_signature_and_claim_binding(self):
        registry = ReleaseRegistry(); manifest = registry.publish("a", "1.0.0", {"README.md": b"x"}, published_at="2026-08-13T00:00:00Z")
        attestation = PublisherAttestation("ES256", "key-1", "org", "lskills-api", "skills.publish", signature=b"sig")
        attestation.verify(manifest, verifier=lambda key, claims, sig: key == "key-1" and sig == b"sig" and b"a@1.0.0" in claims, organization="org", audience="lskills-api", capability="skills.publish")
        with self.assertRaises(ReleaseError): attestation.verify(manifest, verifier=lambda *_: False, organization="org", audience="lskills-api", capability="skills.publish")
        with self.assertRaises(ReleaseError): PublisherAttestation("RS256", "k", "org", "lskills-api", "skills.publish").verify_metadata(organization="org", audience="lskills-api", capability="skills.publish")
