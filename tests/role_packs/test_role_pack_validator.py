#!/usr/bin/env python3
"""PKT-22/23 role-pack admission contradiction tests."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "role-packs"))

from role_pack_validator import load_role_pack_inputs, validate_role_pack  # noqa: E402


COLLECTION = ROOT / "collections" / "google-workspace"


def read(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    assert isinstance(value, dict)
    return value


def collection_inputs() -> tuple[dict, list[dict], list[dict]]:
    manifest = read(COLLECTION / "role-pack-manifest.json")
    releases = [read(path) for path in sorted((COLLECTION / "releases").glob("*.json"))]
    eligibilities = [read(path) for path in sorted((COLLECTION / "eligibility").glob("*.json"))]
    return manifest, releases, eligibilities


class RolePackValidatorTests(unittest.TestCase):
    def test_present_google_role_pack_remains_hold(self) -> None:
        result = load_role_pack_inputs(
            COLLECTION / "role-pack-manifest.json",
            COLLECTION / "releases",
            COLLECTION / "eligibility",
        )
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["admitted"])
        self.assertEqual(result["proof_scope"], "source")
        self.assertEqual(result["release_reference_count"], 7)
        codes = [item["code"] for item in result["violations"]]
        self.assertEqual(codes.count("release_not_qualified"), 7)
        self.assertEqual(codes.count("eligibility_not_eligible"), 7)
        self.assertEqual(codes.count("eligibility_gate_not_satisfied"), 28)

    def test_committed_contradiction_evidence_is_explicitly_non_admitting(self) -> None:
        evidence = read(ROOT / "role-packs" / "pkt-22-23-contradiction.json")
        self.assertEqual(evidence["status"], "HOLD")
        self.assertFalse(evidence["admitted"])
        self.assertFalse(evidence["claims"]["qualified_release"])
        self.assertFalse(evidence["claims"]["provider_live"])
        self.assertFalse(evidence["claims"]["consumer"])
        self.assertFalse(evidence["claims"]["vps"])
        self.assertFalse(evidence["claims"]["production"])

    def test_repair_receipt_binds_rejected_checkpoint_and_preserves_holds(self) -> None:
        evidence = read(ROOT / "role-packs" / "pkt-22-23-contradiction.json")
        receipt = evidence["repair_receipt"]

        self.assertEqual(receipt["issue"], 236)
        self.assertEqual(
            receipt["rejected_checkpoint"],
            {
                "commit": "804b1a0af5548efde2a15297d1f911ac14f46c28",
                "tree": "60a93f43babf50999f0e2e9425ecb03c411791f1",
                "parent": "9c219c97ba0a6d7aad05bc7c87eb117405863855",
                "parent_tree": "93400142d8ebd338cc5aaf47fd4904da3a46449c",
            },
        )
        self.assertEqual(
            receipt["protected_base"],
            {
                "ref": "origin/development",
                "commit": "9c219c97ba0a6d7aad05bc7c87eb117405863855",
                "tree": "93400142d8ebd338cc5aaf47fd4904da3a46449c",
            },
        )
        self.assertEqual(
            receipt["rejection_findings"],
            ["stale-generated-secret-fixture-closure", "stale-secret-scan-fixture-binding"],
        )
        self.assertEqual(receipt["generated_output_closure"]["status"], "PASS")
        self.assertEqual(receipt["secret_scan"]["status"], "PASS")
        self.assertFalse(evidence["claims"]["qualification_admission"])
        self.assertFalse(evidence["claims"]["selectability"])
        self.assertFalse(evidence["claims"]["provider_live"])
        self.assertFalse(evidence["claims"]["consumer"])
        self.assertFalse(evidence["claims"]["hosted_stage"])
        self.assertFalse(evidence["claims"]["vps"])
        self.assertFalse(evidence["claims"]["e2e"])
        self.assertFalse(evidence["claims"]["production"])

    def test_missing_exact_release_fails_closed_without_substitution(self) -> None:
        manifest, _, eligibilities = collection_inputs()
        result = validate_role_pack(manifest, [], eligibilities)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["admitted"])
        self.assertEqual(sum(item["code"] == "release_missing" for item in result["violations"]), 7)

    def test_digest_mismatch_is_not_repaired(self) -> None:
        manifest, releases, eligibilities = collection_inputs()
        original = copy.deepcopy(manifest)
        manifest["release_refs"][0]["artifact_digest"] = "sha256:" + ("0" * 64)
        result = validate_role_pack(manifest, releases, eligibilities)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["admitted"])
        self.assertIn("artifact_digest_mismatch", {item["code"] for item in result["violations"]})
        self.assertNotEqual(manifest, original)

    def test_activation_and_identity_tampering_fail_closed(self) -> None:
        manifest, releases, eligibilities = collection_inputs()
        manifest["activation"]["enabled"] = True
        manifest["activation"]["activation_owner"] = "linkskills"
        result = validate_role_pack(manifest, releases, eligibilities)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["admitted"])
        codes = {item["code"] for item in result["violations"]}
        self.assertIn("activation_must_remain_disabled", codes)
        self.assertIn("activation_owner_must_be_consumer", codes)
        self.assertIn("manifest_schema_invalid", codes)

    def test_eligibility_must_bind_to_the_same_exact_release(self) -> None:
        manifest, releases, eligibilities = collection_inputs()
        target_ref = manifest["release_refs"][0]["eligibility_ref"]
        target_id = target_ref.removeprefix("opaque:eligibility:")
        target = next(item for item in eligibilities if item["eligibility_id"] == target_id)
        target["release_id"] = "other-release@0.0.1"
        result = validate_role_pack(manifest, releases, eligibilities)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["admitted"])
        self.assertIn("eligibility_release_mismatch", {item["code"] for item in result["violations"]})

    def test_conflicting_duplicate_release_identity_is_hold(self) -> None:
        manifest, releases, eligibilities = collection_inputs()
        release_id = manifest["release_refs"][0]["release_id"]
        original = next(item for item in releases if item["release_id"] == release_id)
        conflicting = copy.deepcopy(original)
        conflicting["bundle_hash"] = "sha256:" + ("0" * 64)

        result = validate_role_pack(manifest, [original, conflicting], eligibilities)

        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["admitted"])
        self.assertIn(
            "conflicting_duplicate_release_identity",
            {item["code"] for item in result["violations"]},
        )

    def test_conflicting_duplicate_eligibility_identity_is_hold(self) -> None:
        manifest, releases, eligibilities = collection_inputs()
        eligibility_id = manifest["release_refs"][0]["eligibility_ref"].removeprefix(
            "opaque:eligibility:"
        )
        original = next(item for item in eligibilities if item["eligibility_id"] == eligibility_id)
        conflicting = copy.deepcopy(original)
        conflicting["release_id"] = "different-release@0.0.1"

        result = validate_role_pack(manifest, releases, [original, conflicting])

        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["admitted"])
        self.assertIn(
            "conflicting_duplicate_eligibility_identity",
            {item["code"] for item in result["violations"]},
        )

    def test_report_is_deterministic_and_inputs_are_not_mutated(self) -> None:
        manifest, releases, eligibilities = collection_inputs()
        before = (copy.deepcopy(manifest), copy.deepcopy(releases), copy.deepcopy(eligibilities))
        first = validate_role_pack(manifest, releases, eligibilities)
        second = validate_role_pack(manifest, releases, eligibilities)
        self.assertEqual(first, second)
        self.assertEqual((manifest, releases, eligibilities), before)


if __name__ == "__main__":
    unittest.main()
