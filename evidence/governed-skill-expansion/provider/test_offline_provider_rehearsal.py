"""Focused tests for the PKT-25 local-only rehearsal and identity binding."""

from __future__ import annotations

import unittest

from offline_provider_rehearsal import LOOPBACK_ENDPOINT, default_identity, rehearse
from package_receipt import PackageIdentityError, bind_receipt, package_identity


IDENTITY = {
    "repository": "https://github.com/linktrend/LiNKskills",
    "ref": "refs/heads/issue/local-rehearsal",
    "commit": "a" * 40,
    "tree": "b" * 40,
}


class OfflineProviderRehearsalTests(unittest.TestCase):
    def test_rehearsal_is_local_and_all_checks_pass(self) -> None:
        receipt = rehearse(IDENTITY)
        self.assertEqual(receipt["status"], "LOCAL_ONLY")
        self.assertEqual(receipt["endpoint"], LOOPBACK_ENDPOINT)
        self.assertTrue(receipt["rehearsal"]["all_checks_pass"])
        self.assertFalse(receipt["safety"]["network_contacted"])
        self.assertFalse(receipt["claims"]["provider_live"])
        self.assertEqual(receipt["receipt_digest"], receipt["receipt_sha256"])

    def test_identity_rejects_symbolic_ref_and_bad_sha(self) -> None:
        with self.assertRaises(PackageIdentityError):
            package_identity(**{**IDENTITY, "ref": "HEAD"}, package_id="x", package_version="1", package_bytes=b"x", manifest={})
        with self.assertRaises(PackageIdentityError):
            package_identity(**{**IDENTITY, "commit": "a" * 64}, package_id="x", package_version="1", package_bytes=b"x", manifest={})

    def test_source_binding_rejects_checkout_mismatch(self) -> None:
        identity = package_identity(**IDENTITY, package_id="x", package_version="1.0.0", package_bytes=b"x", manifest={})
        with self.assertRaises(PackageIdentityError):
            bind_receipt({"status": "LOCAL_ONLY"}, identity, result_digest="c" * 64,
                         checkout_identity={**IDENTITY, "tree": "d" * 40}, provider_identity=IDENTITY)

    def test_origin_suffixes_normalize_for_source_binding(self) -> None:
        identity = package_identity(**{**IDENTITY, "repository": IDENTITY["repository"] + ".git"}, package_id="x", package_version="1.0.0", package_bytes=b"x", manifest={})
        receipt = bind_receipt({"status": "LOCAL_ONLY"}, identity, result_digest="c" * 64,
                               checkout_identity=IDENTITY, provider_identity={**IDENTITY, "repository": IDENTITY["repository"] + ".git"})
        self.assertEqual(receipt["source_binding"]["checkout"]["repository"], IDENTITY["repository"])

    def test_credential_userinfo_origin_is_stripped_for_source_binding(self) -> None:
        userinfo_url = "https://ci-user:ci-pass@github.com/linktrend/LiNKskills.git"
        identity = package_identity(**{**IDENTITY, "repository": userinfo_url}, package_id="x", package_version="1.0.0", package_bytes=b"x", manifest={})
        receipt = bind_receipt({"status": "LOCAL_ONLY"}, identity, result_digest="c" * 64,
                               checkout_identity={**IDENTITY, "repository": userinfo_url}, provider_identity=IDENTITY)
        self.assertEqual(receipt["identity"]["repository"], IDENTITY["repository"])
        self.assertEqual(receipt["source_binding"]["checkout"]["repository"], IDENTITY["repository"])

    def test_receipt_ref_rejects_whitespace(self) -> None:
        identity = package_identity(**IDENTITY, package_id="x", package_version="1.0.0", package_bytes=b"x", manifest={})
        with self.assertRaises(PackageIdentityError):
            bind_receipt({}, identity, result_digest="c" * 64, receipt_ref="opaque:bad ref")

    def test_receipt_ref_rejects_absolute_and_parent_paths(self) -> None:
        identity = package_identity(**IDENTITY, package_id="x", package_version="1.0.0", package_bytes=b"x", manifest={})
        for receipt_ref in ("/tmp/receipt.json", "../receipt.json", "receipts/../receipt.json"):
            with self.subTest(receipt_ref=receipt_ref), self.assertRaises(PackageIdentityError):
                bind_receipt({}, identity, result_digest="c" * 64, receipt_ref=receipt_ref)

    def test_default_identity_uses_qualified_git_ref(self) -> None:
        ref = default_identity()["ref"]
        self.assertTrue(ref.startswith(("refs/heads/", "refs/remotes/")))
        self.assertNotEqual(ref, "HEAD")


if __name__ == "__main__":
    unittest.main()
