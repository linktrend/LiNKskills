"""PKT-23 preparatory qualification and selectability guard tests."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evidence" / "governed-skill-expansion"))

from qualification_harness import (  # noqa: E402
    PREPARATORY_STATUS,
    evaluate_release,
    make_preparatory_receipt,
)


DIGEST = "sha256:" + ("a" * 64)
SOURCE_COMMIT = "b" * 40


def release(*, lifecycle_state: str = "usable", profiles: list[str] | None = None) -> dict:
    return {
        "release_id": "research@1.0.0",
        "artifact_id": "research",
        "version": "1.0.0",
        "bundle_hash": DIGEST,
        "lifecycle_state": lifecycle_state,
        "compatible_runtime_profiles": profiles if profiles is not None else ["codex-macos"],
        "provenance": {
            "repository": "https://github.com/linktrend/LiNKskills",
            "source_ref": "development",
            "source_commit": SOURCE_COMMIT,
            "source_path": "skills/research",
        },
    }


def evidence(*, status: str = "uncertified", profile_id: str = "codex-macos") -> dict:
    return {
        "release_id": "research@1.0.0",
        "bundle_hash": DIGEST,
        "source_commit": SOURCE_COMMIT,
        "runtime_profile_id": profile_id,
        "evaluator": {
            "evaluator_id": "eval-runner",
            "evaluator_version": "0.1.0",
            "run_id": "run:research:001",
            "result_digest": DIGEST,
            "release_id": "research@1.0.0",
            "source_commit": SOURCE_COMMIT,
            "bundle_hash": DIGEST,
            "runtime_profile_id": profile_id,
        },
        "qualification": {
            "status": status,
            "evidence_ref": "opaque:evidence:research-001",
            "result_digest": DIGEST,
            "release_id": "research@1.0.0",
            "source_commit": SOURCE_COMMIT,
            "runtime_profile_id": profile_id,
        },
    }


class GovernedSkillQualificationTests(unittest.TestCase):
    def assert_nonselectable(self, result: dict, expected_classification: str) -> None:
        self.assertEqual(result["status"], PREPARATORY_STATUS)
        self.assertFalse(result["selectable"])
        self.assertFalse(result["qualification_pass_claimed"])
        self.assertEqual(result["classification"], expected_classification)
        self.assertEqual(result["dependency"]["packet"], "PKT-22")
        self.assertEqual(result["dependency"]["status"], "unresolved")

    def test_missing_release_identity_is_nonselectable(self) -> None:
        result = evaluate_release({}, evidence(), "codex-macos")
        self.assert_nonselectable(result, "missing")
        self.assertIn("missing_release_identity", result["reason_codes"])

    def test_draft_release_is_nonselectable(self) -> None:
        result = evaluate_release(release(lifecycle_state="draft"), evidence(), "codex-macos")
        self.assert_nonselectable(result, "draft")

    def test_uncertified_release_is_nonselectable(self) -> None:
        result = evaluate_release(release(), evidence(status="uncertified"), "codex-macos")
        self.assert_nonselectable(result, "uncertified")

    def test_incompatible_runtime_profile_is_nonselectable(self) -> None:
        result = evaluate_release(release(profiles=["cursor-macos"]), evidence(status="certified"), "codex-macos")
        self.assert_nonselectable(result, "incompatible")
        self.assertIn("incompatible_runtime_profile", result["reason_codes"])

    def test_identity_mismatch_is_never_repaired_or_substituted(self) -> None:
        supplied_release = release()
        supplied_evidence = evidence()
        supplied_evidence["source_commit"] = "c" * 40
        result = evaluate_release(supplied_release, supplied_evidence, "codex-macos")
        self.assert_nonselectable(result, "identity_mismatch")
        self.assertIn("evidence_source_commit_mismatch", result["reason_codes"])
        self.assertEqual(result["release"]["source"]["source_commit"], SOURCE_COMMIT)

    def test_complete_synthetic_inputs_remain_dependency_blocked(self) -> None:
        result = evaluate_release(release(), evidence(status="certified"), "codex-macos")
        self.assert_nonselectable(result, "dependency_blocked")
        self.assertEqual(result["qualification"]["status"], "certified")
        self.assertFalse(result["qualification_pass_claimed"])

    def test_missing_evaluator_and_qualification_metadata_fail_closed(self) -> None:
        result = evaluate_release(release(), {"release_id": "research@1.0.0"}, "codex-macos")
        self.assert_nonselectable(result, "missing")
        self.assertIn("missing_evaluator_identity", result["reason_codes"])
        self.assertIn("missing_qualification_metadata", result["reason_codes"])

    def test_input_is_not_mutated_and_receipt_is_deterministic(self) -> None:
        supplied_release = release()
        supplied_evidence = evidence()
        before = (copy.deepcopy(supplied_release), copy.deepcopy(supplied_evidence))
        first = evaluate_release(supplied_release, supplied_evidence, "codex-macos")
        second = evaluate_release(supplied_release, supplied_evidence, "codex-macos")
        self.assertEqual((supplied_release, supplied_evidence), before)
        self.assertEqual(first, second)
        receipt_a = make_preparatory_receipt([first, second])
        receipt_b = make_preparatory_receipt([second, first])
        self.assertEqual(receipt_a, receipt_b)
        self.assertEqual(receipt_a["selectable_release_count"], 0)
        unsigned = dict(receipt_a)
        digest = unsigned.pop("receipt_digest")
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        self.assertEqual(digest, "sha256:" + hashlib.sha256(canonical).hexdigest())

    def test_committed_receipt_records_hold_without_a_pass_claim(self) -> None:
        receipt_path = ROOT / "evidence" / "governed-skill-expansion" / "preparatory-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["packet"], "PKT-23")
        self.assertEqual(receipt["status"], PREPARATORY_STATUS)
        self.assertEqual(receipt["dependency"], {
            "packet": "PKT-22",
            "status": "unresolved",
            "required_for": "exact reusable role-pack manifests and role applicability",
            "effect": "no qualification admission or selectability claim",
        })
        self.assertFalse(receipt["qualification_pass_claimed"])
        self.assertEqual(receipt["selectable_release_count"], 0)


if __name__ == "__main__":
    unittest.main()
