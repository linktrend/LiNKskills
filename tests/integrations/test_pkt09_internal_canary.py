"""Focused PKT-09 internal synthetic canary execution guards."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKT09 = ROOT / "evidence" / "governed-skill-expansion" / "pkt09"
sys.path.insert(0, str(PKT09))

from pkt09_internal_canary import (  # noqa: E402
    FALSE_CLAIMS,
    LEDGER_CANDIDATE_COMMIT,
    LEDGER_CANDIDATE_TREE,
    PACKET,
    Pkt09CanaryError,
    bind_internal_canary_receipt,
    inspect_global_eligibility,
    inspect_ledger_admission,
    verify_changed_paths_are_canary_only,
    verify_ledger_candidate,
    verify_source_unmutated,
)


class Pkt09InternalCanaryTests(unittest.TestCase):
    def test_named_ledger_candidate_is_protected_and_admits_pkt09_only(self) -> None:
        candidate = verify_ledger_candidate(ROOT)
        admission = inspect_ledger_admission(ROOT)
        self.assertEqual(candidate["commit"], LEDGER_CANDIDATE_COMMIT)
        self.assertEqual(candidate["tree"], LEDGER_CANDIDATE_TREE)
        self.assertTrue(candidate["protected"])
        self.assertEqual(admission["first_packet"], PACKET)
        self.assertEqual(admission["implementation_status"], "SOURCE_LANDED_DO_NOT_DUPLICATE")
        self.assertEqual(admission["decision"], "HOLD")

    def test_all_207_members_remain_globally_ineligible(self) -> None:
        eligibility = inspect_global_eligibility(ROOT)
        self.assertEqual(eligibility["member_count"], 207)
        self.assertEqual(eligibility["ineligible_count"], 207)
        self.assertEqual(eligibility["ordinary_selectable_count"], 0)
        self.assertEqual(eligibility["stable_qualified_count"], 0)
        self.assertEqual(eligibility["approved_internal_canary"], 182)

    def test_pkt09_source_is_not_reimplemented_against_development(self) -> None:
        development = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "refs/remotes/origin/development"],
            text=True,
        ).strip()
        self.assertEqual(verify_source_unmutated(ROOT, development), [])

    def test_out_of_lane_paths_are_rejected(self) -> None:
        with self.assertRaises(Pkt09CanaryError) as raised:
            verify_changed_paths_are_canary_only(["skills/operational-reporting/SKILL.md"])
        self.assertIn("changed_path_outside_pkt09_canary_lane", str(raised.exception))

    def test_bound_receipt_keeps_holds_and_one_executor(self) -> None:
        receipt = bind_internal_canary_receipt(ROOT, run_checks=True)
        self.assertEqual(receipt["packet"], PACKET)
        self.assertEqual(receipt["admitted_packets"], [PACKET])
        self.assertTrue(receipt["executor"]["one_executor_per_packet"])
        self.assertFalse(receipt["broad_full_suite"])
        self.assertFalse(receipt["live_vps_staging_main_production"])
        self.assertFalse(receipt["completion_claimed"])
        self.assertEqual(receipt["status"], "INTERNAL_SYNTHETIC_CANARY_HOLD")
        self.assertEqual(receipt["decision"], "HOLD")
        for key in FALSE_CLAIMS:
            self.assertFalse(receipt["claims"][key], msg=key)
        self.assertEqual(len(receipt["focused_checks"]), 3)
        self.assertTrue(all(item["status"] == "PASS" for item in receipt["focused_checks"]))
        self.assertEqual(receipt["eligibility"]["ineligible_count"], 207)
        receipt_path = PKT09 / "internal-synthetic-canary-receipt.json"
        on_disk = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.is_file() else receipt
        self.assertEqual(on_disk["packet"], PACKET)
        self.assertFalse(on_disk["claims"]["provider_live"])
        self.assertFalse(on_disk["claims"]["consumer"])


if __name__ == "__main__":
    unittest.main()
