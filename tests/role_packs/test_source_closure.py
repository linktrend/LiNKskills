#!/usr/bin/env python3
"""PKT-22 exact-source dependency closure and truthful HOLD tests."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "core"))
sys.path.insert(0, str(ROOT / "role-packs"))

from role_pack_validator import load_role_pack_inputs  # noqa: E402
from source_metadata import (  # noqa: E402
    PROTECTED_BASE,
    FALSE_CLAIMS,
    MANIFEST_STEMS,
    RELEASE_DIR,
    ELIGIBILITY_DIR,
    ROLE_PACK_DIR,
    bundle_hash_at_source,
    make_source_receipt,
    referenced_release_ids,
    skill_id_from_release_id,
    verify_release_records_match_source,
    verify_source_identity,
)


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


class RolePackSourceClosureTests(unittest.TestCase):
    def test_recorded_source_identity_is_a_real_git_commit_tree(self) -> None:
        """Receipt and module bind the same historical commit/tree, not live HEAD."""
        committed = read(ROLE_PACK_DIR / "pkt-22-source-receipt.json")
        recorded = committed["protected_base"]
        resolved = verify_source_identity(recorded)
        self.assertEqual(resolved, PROTECTED_BASE)
        self.assertEqual(recorded, PROTECTED_BASE)
        git_commit = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", recorded["commit"]],
            text=True,
        ).strip()
        git_tree = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", f"{recorded['commit']}^{{tree}}"],
            text=True,
        ).strip()
        self.assertEqual(git_commit, recorded["commit"])
        self.assertEqual(git_tree, recorded["tree"])
        live_commit = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            text=True,
        ).strip()
        # Metadata commits may move HEAD; the recorded skill-tree identity stays frozen.
        self.assertEqual(len(recorded["commit"]), 40)
        self.assertEqual(len(recorded["tree"]), 40)
        self.assertTrue(git_commit)
        self.assertNotEqual(recorded["commit"], "2e03130b5d8e801a066da504e6ff444f1ff3d46c")
        self.assertIsInstance(live_commit, str)

    def test_every_release_bundle_hash_matches_recorded_historical_source(self) -> None:
        """Hashes are proven from git archive of the recorded commit, not live tree only."""
        source = verify_release_records_match_source()
        self.assertEqual(source, PROTECTED_BASE)
        stale = {
            "ref": PROTECTED_BASE["ref"],
            "commit": "2e03130b5d8e801a066da504e6ff444f1ff3d46c",
            "tree": "3d3c3b1df7e1485b8f56607fbfe499d3403bf7ea",
        }
        mismatches = 0
        for release_id in referenced_release_ids():
            skill_id = skill_id_from_release_id(release_id)
            record = read(RELEASE_DIR / f"{skill_id}.json")
            historical = bundle_hash_at_source(skill_id, source["commit"])
            stale_hash = bundle_hash_at_source(skill_id, stale["commit"])
            self.assertEqual(record["bundle_hash"], historical["bundle_hash"], msg=release_id)
            self.assertEqual(record["source_commit"], source["commit"])
            self.assertEqual(record["source_tree"], source["tree"])
            if record["bundle_hash"] != stale_hash["bundle_hash"]:
                mismatches += 1
        self.assertGreater(
            mismatches,
            0,
            "recorded hashes must not also match an unrelated older commit (live-tree-only false pass)",
        )

    def test_every_reference_binds_an_exact_skill_tree_digest(self) -> None:
        """Dependency closure uses computed skill-tree identity, not placeholders."""
        source = verify_source_identity(PROTECTED_BASE)
        for release_id in referenced_release_ids():
            skill_id = skill_id_from_release_id(release_id)
            skill_dir = ROOT / "skills" / skill_id
            self.assertTrue(skill_dir.is_dir(), msg=release_id)
            historical = bundle_hash_at_source(skill_id, source["commit"])
            record = read(RELEASE_DIR / f"{skill_id}.json")
            self.assertEqual(record["release_id"], release_id)
            self.assertEqual(record["bundle_hash"], historical["bundle_hash"])
            self.assertEqual(record["source_commit"], source["commit"])
            self.assertEqual(record["source_tree"], source["tree"])
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
