#!/usr/bin/env python3
"""PKT-03 external collection lifecycle proofs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "publisher"))

from linkskills_publisher.external_lifecycle import (  # noqa: E402
    ExternalCollectionLifecycle,
    LifecycleError,
)


class ExternalLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lifecycle = ExternalCollectionLifecycle()
        self.verify_signature = lambda signer, digest, signature: signer == "autowork"
        self.vendor = self.lifecycle.ingest_vendor_release(
            "vendor-tools",
            {"SKILL.md": b"vendor bytes", "references/eval.yaml": b"pass: true\n"},
            vendor="Acme",
            repository="https://example.invalid/acme/tools",
            publisher="Acme Publishing",
            license_ref="Apache-2.0",
            source_ref="v1.2.3",
            source_path="skills/demo",
        )

    def evidence(self):
        return {key: {"status": "reviewed"} for key in ExternalCollectionLifecycle.REVIEW_EVIDENCE}

    def test_vendor_bytes_inventory_and_per_file_lineage_are_immutable(self):
        self.assertEqual(self.vendor.files["SKILL.md"], b"vendor bytes")
        self.assertEqual(self.vendor.file_provenance[0].license_ref, "Apache-2.0")
        self.assertFalse(self.vendor.selectable)
        replay = self.lifecycle.ingest_vendor_release(
            "vendor-tools",
            {"SKILL.md": b"vendor bytes", "references/eval.yaml": b"pass: true\n"},
            vendor="Acme", repository="https://example.invalid/acme/tools",
            publisher="Acme Publishing", license_ref="Apache-2.0", source_ref="v1.2.3",
            source_path="skills/demo", release_id=self.vendor.release_id,
        )
        self.assertEqual(replay.inventory_digest, self.vendor.inventory_digest)
        with self.assertRaisesRegex(LifecycleError, "immutable_vendor_release_conflict"):
            self.lifecycle.ingest_vendor_release(
                "vendor-tools", {"SKILL.md": b"changed"}, vendor="Acme",
                repository="https://example.invalid/acme/tools", publisher="Acme Publishing",
                license_ref="Apache-2.0", source_ref="v1.2.3", release_id=self.vendor.release_id,
            )

    def test_adaptation_links_to_vendor_without_mutating_original(self):
        adapted = self.lifecycle.register_adaptation(
            "vendor-tools", self.vendor.release_id, {"SKILL.md": b"adapted bytes"},
            adaptation_ref="linktrend/demo-v1", qualification="qualified", selectable=True,
        )
        self.assertEqual(adapted.base_vendor_release_id, self.vendor.release_id)
        self.assertTrue(adapted.selectable)
        self.assertEqual(self.vendor.files["SKILL.md"], b"vendor bytes")

    def test_candidate_delivery_is_signed_idempotent_and_does_not_switch_current(self):
        adapted = self.lifecycle.register_adaptation(
            "vendor-tools", self.vendor.release_id, {"SKILL.md": b"safe adapted"},
            adaptation_ref="linktrend/demo-v1", qualification="qualified", selectable=True,
        )
        candidate = self.lifecycle.submit_update_candidate(
            "vendor-tools", adapted.release_id, idempotency_key="poll:1",
            signature="sig", signer="autowork", verify_signature=self.verify_signature,
        )
        self.assertIsNone(self.lifecycle.current_release("vendor-tools"))
        replay = self.lifecycle.submit_update_candidate(
            "vendor-tools", adapted.release_id, idempotency_key="poll:1",
            signature="sig", signer="autowork", verify_signature=self.verify_signature,
        )
        self.assertEqual(replay.candidate_id, candidate.candidate_id)
        with self.assertRaisesRegex(LifecycleError, "idempotency_conflict"):
            self.lifecycle.submit_update_candidate(
                "vendor-tools", adapted.release_id, idempotency_key="poll:1",
                signature="different", signer="autowork", verify_signature=self.verify_signature,
            )
        with self.assertRaisesRegex(LifecycleError, "platform_apply_receipt_required"):
            self.lifecycle.apply_candidate(candidate.candidate_id)

    def test_review_and_platform_receipts_are_required_for_apply(self):
        adapted = self.lifecycle.register_adaptation(
            "vendor-tools", self.vendor.release_id, {"SKILL.md": b"safe adapted"},
            adaptation_ref="linktrend/demo-v1", qualification="qualified", selectable=True,
        )
        candidate = self.lifecycle.submit_update_candidate(
            "vendor-tools", adapted.release_id, idempotency_key="poll:2",
            signature="sig", signer="autowork", verify_signature=self.verify_signature,
        )
        review = self.lifecycle.review_candidate(
            candidate.candidate_id, "accept", self.evidence(), reviewer="librarian",
        )
        self.assertEqual(review.status, "accepted_pending_platform")
        with self.assertRaisesRegex(LifecycleError, "platform_authority_required"):
            self.lifecycle.record_platform_review_receipt(
                candidate.candidate_id,
                {"receipt_id": "r1", "authority": "librarian", "candidate_digest": candidate.candidate_digest, "decision": "accept"},
            )
        self.lifecycle.record_platform_review_receipt(
            candidate.candidate_id,
            {"receipt_id": "r1", "authority": "LiNKplatform", "candidate_digest": candidate.candidate_digest, "decision": "accept"},
        )
        self.lifecycle.record_platform_apply_receipt(
            candidate.candidate_id,
            {"receipt_id": "a1", "authority": "LiNKplatform", "operation": "apply", "candidate_digest": candidate.candidate_digest, "release_id": adapted.release_id, "applied": True},
        )
        self.assertEqual(self.lifecycle.current_release("vendor-tools"), adapted.release_id)

    def test_rollback_requires_platform_receipt_and_cas(self):
        qualified_vendor = self.lifecycle.ingest_vendor_release(
            "vendor-tools", {"SKILL.md": b"vendor bytes", "references/eval.yaml": b"pass: true\n"},
            vendor="Acme", repository="https://example.invalid/acme/tools",
            publisher="Acme Publishing", license_ref="Apache-2.0", source_ref="v1.2.3",
            source_path="skills/demo", qualification="qualified", release_id="vendor-tools-safe-v1",
        )
        adapted = self.lifecycle.register_adaptation(
            "vendor-tools", self.vendor.release_id, {"SKILL.md": b"adapted"},
            adaptation_ref="linktrend/demo-v1", qualification="qualified", selectable=True,
        )
        candidate = self.lifecycle.submit_update_candidate(
            "vendor-tools", adapted.release_id, idempotency_key="poll:3", signature="sig", signer="autowork",
            verify_signature=self.verify_signature,
        )
        self.lifecycle.review_candidate(candidate.candidate_id, "adapt", self.evidence(), reviewer="librarian")
        self.lifecycle.record_platform_review_receipt(
            candidate.candidate_id,
            {"receipt_id": "r2", "authority": "LiNKplatform", "candidate_digest": candidate.candidate_digest, "decision": "adapt"},
        )
        self.lifecycle.record_platform_apply_receipt(
            candidate.candidate_id,
            {"receipt_id": "a2", "authority": "LiNKplatform", "operation": "apply", "candidate_digest": candidate.candidate_digest, "release_id": adapted.release_id, "applied": True},
        )
        with self.assertRaisesRegex(LifecycleError, "rollback_receipt_required"):
            self.lifecycle.rollback_current("vendor-tools", adapted.release_id, expected_current=adapted.release_id, platform_receipt={})
        self.lifecycle.rollback_current(
            "vendor-tools", qualified_vendor.release_id, expected_current=adapted.release_id,
            platform_receipt={"receipt_id": "rb1", "authority": "LiNKplatform", "operation": "rollback", "release_id": qualified_vendor.release_id, "applied": True},
        )
        self.assertEqual(self.lifecycle.current_release("vendor-tools"), qualified_vendor.release_id)

    def test_signature_verifier_is_mandatory_and_false_fails_closed(self):
        adapted = self.lifecycle.register_adaptation(
            "vendor-tools", self.vendor.release_id, {"SKILL.md": b"safe adapted"},
            adaptation_ref="linktrend/demo-v1", qualification="qualified", selectable=True,
        )
        with self.assertRaisesRegex(LifecycleError, "candidate_signature_verifier_required"):
            self.lifecycle.submit_update_candidate(
                "vendor-tools", adapted.release_id, idempotency_key="poll:no-verifier",
                signature="sig", signer="autowork",
            )
        with self.assertRaisesRegex(LifecycleError, "candidate_signature_invalid"):
            self.lifecycle.submit_update_candidate(
                "vendor-tools", adapted.release_id, idempotency_key="poll:bad-signature",
                signature="sig", signer="autowork", verify_signature=lambda *_: False,
            )

    def test_unsafe_path_components_and_collection_ownership_fail_closed(self):
        for path in ("../escape", "nested/../escape", "nested/./file", "/absolute", "nested//file", "nested\\file", "./file"):
            with self.assertRaisesRegex(LifecycleError, "unsafe_file_path"):
                self.lifecycle.ingest_vendor_release(
                    "vendor-tools", {path: b"unsafe"}, vendor="Acme",
                    repository="https://example.invalid/acme/tools", publisher="Acme Publishing",
                    license_ref="Apache-2.0", source_ref="v1.2.3", source_path="skills/demo",
                )
        other = self.lifecycle.ingest_vendor_release(
            "other-collection", {"SKILL.md": b"other"}, vendor="Acme",
            repository="https://example.invalid/acme/tools", publisher="Acme Publishing",
            license_ref="Apache-2.0", source_ref="v1.2.3", source_path="skills/other",
        )
        with self.assertRaisesRegex(LifecycleError, "manifest_release_collection_mismatch"):
            self.lifecycle.create_collection_manifest(
                "vendor-tools", "1.0.0", [other.release_id], source_release="v1.2.3", license_ref="Apache-2.0",
            )
        with self.assertRaisesRegex(LifecycleError, "base_vendor_collection_mismatch"):
            self.lifecycle.register_adaptation(
                "vendor-tools", other.release_id, {"SKILL.md": b"adapted"}, adaptation_ref="bad",
            )

    def test_apply_rejects_rollback_and_identical_receipt_is_idempotent(self):
        adapted = self.lifecycle.register_adaptation(
            "vendor-tools", self.vendor.release_id, {"SKILL.md": b"safe adapted"},
            adaptation_ref="linktrend/demo-v1", qualification="qualified", selectable=True,
        )
        candidate = self.lifecycle.submit_update_candidate(
            "vendor-tools", adapted.release_id, idempotency_key="poll:receipt",
            signature="sig", signer="autowork", verify_signature=self.verify_signature,
        )
        self.lifecycle.review_candidate(candidate.candidate_id, "accept", self.evidence(), reviewer="librarian")
        self.lifecycle.record_platform_review_receipt(
            candidate.candidate_id,
            {"receipt_id": "review-receipt", "authority": "LiNKplatform", "candidate_digest": candidate.candidate_digest, "decision": "accept"},
        )
        rollback_apply = {"receipt_id": "rollback-as-apply", "authority": "LiNKplatform", "operation": "rollback", "candidate_digest": candidate.candidate_digest, "release_id": adapted.release_id, "applied": True}
        with self.assertRaisesRegex(LifecycleError, "apply_receipt_operation_invalid"):
            self.lifecycle.record_platform_apply_receipt(candidate.candidate_id, rollback_apply)
        receipt = {"receipt_id": "apply-receipt", "authority": "LiNKplatform", "operation": "apply", "candidate_digest": candidate.candidate_digest, "release_id": adapted.release_id, "applied": True}
        self.lifecycle.record_platform_apply_receipt(candidate.candidate_id, receipt)
        history_size = len(self.lifecycle.pointer_history)
        replay = self.lifecycle.record_platform_apply_receipt(candidate.candidate_id, receipt)
        self.assertEqual(replay["receipt_id"], "apply-receipt")
        self.assertEqual(len(self.lifecycle.pointer_history), history_size)

    def test_rollback_target_must_belong_to_collection(self):
        other = self.lifecycle.ingest_vendor_release(
            "other-collection", {"SKILL.md": b"other"}, vendor="Acme",
            repository="https://example.invalid/acme/tools", publisher="Acme Publishing",
            license_ref="Apache-2.0", source_ref="v1.2.3", source_path="skills/other",
            qualification="qualified", release_id="other-safe-v1",
        )
        with self.assertRaisesRegex(LifecycleError, "rollback_release_collection_mismatch"):
            self.lifecycle.rollback_current(
                "vendor-tools", other.release_id, expected_current=None,
                platform_receipt={"receipt_id": "rb-other", "authority": "LiNKplatform", "operation": "rollback", "release_id": other.release_id, "applied": True},
            )


if __name__ == "__main__":
    unittest.main()
