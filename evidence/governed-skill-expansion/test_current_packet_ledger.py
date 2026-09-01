"""Focused tests for the current exact packet ledger."""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEDGER = Path(__file__).with_name("current-packet-ledger.json")
MANIFEST = ROOT / "docs" / "planning" / "governed-skill-expansion" / "EXECUTION-MANIFEST.json"
PKT22 = ROOT / "role-packs" / "pkt-22-source-receipt.json"
SEED = ROOT / "evidence" / "initial-skill-seed" / "member-classification.json"
CANARY = ROOT / "evidence" / "initial-skill-seed" / "canary-publication-receipt.json"
FALSE_CLAIMS = (
    "activation",
    "consumer",
    "e2e",
    "hosted_stage",
    "production",
    "provider_live",
    "qualification_admission",
    "ordinary_selectability",
    "vps",
    "current_pointer",
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_digest(payload: dict) -> str:
    without = {key: value for key, value in payload.items() if key != "receipt_digest"}
    encoded = json.dumps(without, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + _sha256_bytes(encoded)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


class CurrentPacketLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_ledger_binds_protected_development_identity(self) -> None:
        """Protected base is the exact #307 merge and remains an ancestor of HEAD."""
        protected = self.ledger["protected_base"]
        self.assertEqual(protected["repository"], "linktrend/LiNKskills")
        self.assertEqual(protected["ref"], "refs/remotes/origin/development")
        self.assertEqual(protected["commit"], "4324d41fe6a7a6883075e9baa9a5a7f71dd13b3d")
        self.assertEqual(protected["tree"], "7c5a36f8773ebe9bac417d42a8a48a286fe5968d")
        self.assertEqual(protected["merged_pull_request"], 307)
        self.assertEqual(protected["merged_issue"], 299)
        head = _git("rev-parse", "HEAD")
        origin = _git("rev-parse", "origin/development")
        for label, rev in (("HEAD", head), ("origin/development", origin)):
            ancestor = subprocess.call(
                ["git", "merge-base", "--is-ancestor", protected["commit"], rev],
                cwd=ROOT,
            )
            self.assertEqual(ancestor, 0, msg=f"protected commit must be an ancestor of {label}")

    def test_planning_manifest_remains_plan_and_unmodified_digest(self) -> None:
        """This worker must not refresh or execute the planning manifest."""
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        digest = "sha256:" + _sha256_bytes(MANIFEST.read_bytes())
        self.assertEqual(digest, "sha256:c14c3ccdb612d9bee2be2a4d4ff71358e98cff63e6f09c9f58ac9e49816e7263")
        self.assertEqual(manifest["baseline"]["commit"], "2896fd89726f0b20258ec5a7bba55ccc6299ceb6")
        states = {packet["executionState"] for packet in manifest["packets"]}
        self.assertEqual(states, {"PLAN"})
        self.assertEqual(self.ledger["planning_manifest"]["digest"], digest)
        self.assertEqual(self.ledger["planning_manifest"]["execution_state"], "PLAN")
        self.assertFalse(self.ledger["planning_manifest"]["mutated_by_this_ledger"])

    def test_false_claims_and_hold_decision(self) -> None:
        """Provider, selectability, live, and consumer claims stay false."""
        self.assertEqual(self.ledger["decision"], "HOLD")
        self.assertFalse(self.ledger["completion_claimed"])
        for claim in FALSE_CLAIMS:
            self.assertFalse(self.ledger["claims"][claim], msg=claim)
        self.assertEqual(self.ledger["managed_core"]["package_version"], "2.5.2")
        self.assertEqual(self.ledger["managed_core"]["mutation"], "read_only")

    def test_first_internal_canary_is_pkt_09_and_already_landed(self) -> None:
        """Wave-2 first packet is PKT-09; duplicate implementation is forbidden."""
        canary = self.ledger["first_dependency_ready_internal_canary"]
        self.assertEqual(canary["packet_id"], "PKT-09")
        self.assertEqual(canary["implementation_status"], "SOURCE_LANDED_DO_NOT_DUPLICATE")
        self.assertEqual(canary["next_authorized_skills_mutation"], "none")
        packets = {row["id"]: row for row in self.ledger["packets"]}
        self.assertEqual(packets["PKT-08"]["source_classification"], "SOURCE_LANDED")
        self.assertEqual(packets["PKT-09"]["source_classification"], "SOURCE_LANDED")
        self.assertEqual(packets["PKT-22"]["source_classification"], "SOURCE_LANDED_HOLD")
        self.assertEqual(packets["PKT-23"]["source_classification"], "PREPARATORY_ONLY")
        self.assertEqual(packets["PKT-23"]["dependency_ready"], False)

    def test_pkt22_and_issue299_holds_are_copied_not_upgraded(self) -> None:
        """Existing HOLD receipts are preserved, not inferred into admission."""
        pkt22 = json.loads(PKT22.read_text(encoding="utf-8"))
        self.assertEqual(pkt22["status"], "HOLD")
        self.assertFalse(pkt22["admitted"])
        self.assertFalse(pkt22["claims"]["selectability"])
        self.assertFalse(pkt22["claims"]["provider_live"])
        seed = json.loads(SEED.read_text(encoding="utf-8"))
        publication = json.loads(CANARY.read_text(encoding="utf-8"))
        overlay = self.ledger["issue_299_overlay"]
        self.assertEqual(overlay["member_count"], len(seed["members"]))
        self.assertEqual(overlay["approved_internal_canary"], 182)
        self.assertEqual(overlay["ordinary_selectable_count"], 0)
        self.assertEqual(overlay["stable_qualified_count"], 0)
        self.assertFalse(publication["ordinary_selectability"])
        self.assertFalse(publication["live_provider_publication"])
        self.assertFalse(publication["consumer_activation"])
        self.assertFalse(publication["current_pointer_changed"])

    def test_receipt_digest_matches_canonical_payload(self) -> None:
        """Ledger digest is bound to canonical JSON without the digest field."""
        self.assertEqual(self.ledger["receipt_digest"], _canonical_digest(self.ledger))
        packet_ids = [row["id"] for row in self.ledger["packets"]]
        self.assertEqual(
            packet_ids,
            [f"PKT-{index:02d}" for index in range(27)] + [f"XPKT-{index:02d}" for index in range(1, 6)],
        )


if __name__ == "__main__":
    unittest.main()
