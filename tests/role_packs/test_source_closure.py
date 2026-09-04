#!/usr/bin/env python3
"""PKT-22 exact-source dependency closure and truthful HOLD tests."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "core"))
sys.path.insert(0, str(ROOT / "role-packs"))

from linkskills_core.hashing import build_skill_bundle_manifest  # noqa: E402
from role_pack_validator import load_role_pack_inputs  # noqa: E402
from source_metadata import (  # noqa: E402
    PROTECTED_BASE,
    FALSE_CLAIMS,
    MANIFEST_STEMS,
    RELEASE_DIR,
    ELIGIBILITY_DIR,
    ROLE_PACK_DIR,
    make_source_receipt,
    referenced_release_ids,
    skill_id_from_release_id,
)


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


class RolePackSourceClosureTests(unittest.TestCase):
    def test_every_reference_binds_an_exact_skill_tree_digest(self) -> None:
        """Dependency closure uses computed skill-tree identity, not placeholders."""
        for release_id in referenced_release_ids():
            skill_id = skill_id_from_release_id(release_id)
            skill_dir = ROOT / "skills" / skill_id
            self.assertTrue(skill_dir.is_dir(), msg=release_id)
            bundle = build_skill_bundle_manifest(skill_dir)
            record = read(RELEASE_DIR / f"{skill_id}.json")
            self.assertEqual(record["release_id"], release_id)
            self.assertEqual(record["bundle_hash"], bundle["bundle_hash"])
            self.assertEqual(record["source_commit"], PROTECTED_BASE["commit"])
            self.assertEqual(record["lifecycle_state"], "draft")
            self.assertFalse(record.get("execution_profiles") and record["lifecycle_state"] == "qualified")

    def test_five_manifests_rebind_to_exact_records_and_remain_hold(self) -> None:
        """Schema-valid packs are present, but admission stays HOLD."""
        self.assertEqual(len(MANIFEST_STEMS), 5)
        for stem in MANIFEST_STEMS:
            manifest = read(ROLE_PACK_DIR / f"{stem}.json")
            result = load_role_pack_inputs(
                ROLE_PACK_DIR / f"{stem}.json",
                RELEASE_DIR,
                ELIGIBILITY_DIR,
                ROLE_PACK_DIR / "qualifications",
            )
            self.assertEqual(result["status"], "HOLD")
            self.assertFalse(result["admitted"])
            self.assertEqual(result["claims"], FALSE_CLAIMS)
            codes = {item["code"] for item in result["violations"]}
            self.assertIn("qualification_evidence_missing", codes)
            self.assertIn("release_not_qualified", codes)
            self.assertIn("release_not_selectable", codes)
            self.assertIn("eligibility_not_eligible", codes)
            self.assertFalse(manifest["activation"]["enabled"])
            for entry in manifest["release_refs"]:
                record = read(RELEASE_DIR / f"{skill_id_from_release_id(entry['release_id'])}.json")
                self.assertEqual(entry["artifact_digest"], record["bundle_hash"])
                self.assertEqual(entry["eligibility_ref"], record["eligibility_ref"])

    def test_committed_receipt_matches_live_hold_without_pass_claims(self) -> None:
        """The source receipt is deterministic and does not admit qualification."""
        live = make_source_receipt()
        committed = read(ROLE_PACK_DIR / "pkt-22-source-receipt.json")
        closure = read(ROLE_PACK_DIR / "qualification-closure.json")
        self.assertEqual(committed, live)
        self.assertEqual(committed["status"], "HOLD")
        self.assertFalse(committed["admitted"])
        self.assertEqual(committed["protected_base"], PROTECTED_BASE)
        self.assertEqual(committed["claims"], FALSE_CLAIMS)
        self.assertFalse(committed["qualification_records_present"])
        self.assertEqual(set(committed["hold_role_pack_ids"]), set(MANIFEST_STEMS))
        self.assertEqual(closure["state"], "HOLD")
        self.assertEqual(closure["receipt_digest"], committed["receipt_digest"])
        self.assertEqual(closure["claims"], FALSE_CLAIMS)
        self.assertFalse((ROLE_PACK_DIR / "qualifications").exists())

    def test_negative_activation_and_credential_fields_remain_absent(self) -> None:
        """Role packs never carry identity, credentials, pins, or skill bodies."""
        forbidden = {
            "identity",
            "credential",
            "credentials",
            "private_data",
            "account_binding",
            "account",
            "live_pin",
            "skill_body",
        }
        for stem in MANIFEST_STEMS:
            payload = read(ROLE_PACK_DIR / f"{stem}.json")
            keys: set[str] = set()

            def collect(value: object) -> None:
                if isinstance(value, dict):
                    keys.update(value)
                    for child in value.values():
                        collect(child)
                elif isinstance(value, list):
                    for child in value:
                        collect(child)

            collect(payload)
            self.assertTrue(keys.isdisjoint(forbidden), msg=stem)
            self.assertEqual(payload["activation"]["activation_owner"], "consumer")


if __name__ == "__main__":
    unittest.main()
