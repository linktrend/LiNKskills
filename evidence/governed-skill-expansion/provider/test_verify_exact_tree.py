"""Focused tests for the PKT-25 exact-tree rehearsal."""

from __future__ import annotations

import unittest

from verify_exact_tree import (
    BASE_COMMIT,
    BASE_TREE,
    OWNED_PREFIX,
    VerificationError,
    make_receipt,
    normalize_origin,
    normalize_ref,
    verify_checkout_identity,
    verify_provider_source,
    verify_scope,
)


COMMIT = "a" * 40
TREE = "b" * 40


class ExactTreeVerificationTests(unittest.TestCase):
    def test_origin_and_ref_normalize_without_losing_exact_identity(self) -> None:
        self.assertEqual(normalize_origin("git@github.com:linktrend/LiNKskills.git"), "ssh://github.com/linktrend/LiNKskills")
        self.assertEqual(normalize_ref("development"), "refs/heads/development")
        self.assertEqual(normalize_ref("refs/remotes/origin/development"), "refs/remotes/origin/development")

    def test_ambiguous_identity_fails_closed(self) -> None:
        with self.assertRaises(VerificationError):
            normalize_ref("HEAD")
        self.assertEqual(
            normalize_origin("https://ci-user:ci-pass@github.com/linktrend/LiNKskills.git"),
            "https://github.com/linktrend/LiNKskills",
        )

    def test_checkout_requires_exact_expected_values_and_clean_state(self) -> None:
        observed = {"origin": "https://github.com/linktrend/LiNKskills.git", "ref": "refs/remotes/origin/development", "commit": COMMIT, "tree": TREE, "clean": True}
        result = verify_checkout_identity(observed, {"origin": "https://github.com/linktrend/LiNKskills", "ref": "refs/remotes/origin/development", "commit": COMMIT, "tree": TREE})
        self.assertTrue(all(item["status"] == "PASS" for item in result["checks"].values()))
        mismatch = verify_checkout_identity({**observed, "tree": "c" * 40}, {"tree": TREE})
        self.assertEqual(mismatch["checks"]["tree"]["status"], "FAIL")

    def test_provider_identity_never_passes_with_missing_fields(self) -> None:
        result = verify_provider_source({"repository": "linktrend/LiNKskills", "ref": "development", "commit": COMMIT, "tree": TREE, "paths": [OWNED_PREFIX + "verify_exact_tree.py"]})
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(verify_provider_source(None)["status"], "HOLD")
        self.assertEqual(verify_provider_source({"repository": "linktrend/LiNKskills", "ref": "development", "commit": COMMIT, "tree": TREE, "paths": []})["status"], "HOLD")

    def test_scope_rejects_any_path_leak(self) -> None:
        self.assertEqual(verify_scope([OWNED_PREFIX + "receipt.json"])["status"], "PASS")
        self.assertEqual(verify_scope([".github/linktrend-secret-scan-fixtures.json"])["status"], "PASS")
        result = verify_scope([OWNED_PREFIX + "receipt.json", "catalog/index.json"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["outside_owned_paths"], ["catalog/index.json"])

    def test_receipt_is_always_preparatory_and_dependency_blocked(self) -> None:
        receipt = make_receipt({"origin": "https://github.com/linktrend/LiNKskills", "ref": "refs/remotes/origin/development", "commit": COMMIT, "tree": TREE, "clean": True}, expected_checkout={"origin": "https://github.com/linktrend/LiNKskills", "ref": "refs/remotes/origin/development", "commit": COMMIT, "tree": TREE}, provider_source={"repository": "linktrend/LiNKskills", "ref": "development", "commit": COMMIT, "tree": TREE, "paths": [OWNED_PREFIX + "verify_exact_tree.py"]}, changed_paths=[OWNED_PREFIX + "verify_exact_tree.py"], recorded_at="2026-08-25T00:00:00Z")
        self.assertEqual(receipt["status"], "PREPARATORY_ONLY")
        self.assertEqual(receipt["baseline"]["commit"], BASE_COMMIT)
        self.assertEqual(receipt["baseline"]["tree"], BASE_TREE)
        self.assertEqual(receipt["baseline"]["identity_status"], "PROTECTED_DEVELOPMENT_BASELINE_BINDING_NOT_PROOF")
        self.assertEqual(receipt["dependency"]["status"], "unresolved")
        self.assertFalse(receipt["admission"]["admissible"])
        self.assertFalse(receipt["claims"]["provider_live"])
        self.assertIn("dependency_pkt24_unresolved", receipt["admission"]["reason_codes"])


if __name__ == "__main__":
    unittest.main()
