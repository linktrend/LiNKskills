import unittest

from linkskills_core.release_v2 import ReleaseError, ReleaseManifest, assert_dependency_closure, inventory_digest, sha256


class ReleaseV2(unittest.TestCase):
    def test_inventory_is_deterministic_and_safe(self):
        self.assertEqual(inventory_digest({"a.txt": b"a", "b.txt": b"b"}), inventory_digest({"b.txt": b"b", "a.txt": b"a"}))
        with self.assertRaises(ReleaseError):
            inventory_digest({"../bad": b"x"})

    def test_exact_verify_tamper_lifecycle_and_dependency_fail_closed(self):
        files = {"README.md": b"x"}; digest = inventory_digest(files)
        manifest = ReleaseManifest("a", "1.0.0", digest, sha256({"release_id": "a@1.0.0", "files_digest": digest, "contract_version": "skills-release/0.2"}))
        self.assertEqual(manifest.verify(files), "verified")
        for bad in ({"README.md": b"y"}, {"README.md": b"x", "extra": b"x"}):
            with self.assertRaises(ReleaseError):
                manifest.verify(bad)
        with self.assertRaises(ReleaseError):
            manifest.verify(files, availability="revoked")
        with self.assertRaises(ReleaseError):
            assert_dependency_closure("a@1", {"a@1": ("missing",)})
        with self.assertRaises(ReleaseError):
            assert_dependency_closure("a@1", {"a@1": ("b@1",), "b@1": ("a@1",)})
