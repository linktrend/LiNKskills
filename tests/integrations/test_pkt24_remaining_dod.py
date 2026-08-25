"""Focused PKT-24 remaining-DoD packaging and offline rehearsal guards."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKT24 = ROOT / "evidence" / "governed-skill-expansion" / "pkt24"
sys.path.insert(0, str(PKT24))

from pkt24_rehearsal import (  # noqa: E402
    MIGRATION_MANIFEST,
    Pkt24RehearsalError,
    bind_preparatory_receipt,
    validate_local_fixture,
    validate_migration_manifest,
    validate_receipt,
)


class Pkt24RemainingDodTests(unittest.TestCase):
    @staticmethod
    def _candidate_ref() -> str:
        return "refs/heads/issue/245-repair-pkt-24-receipt-binding-and-loopback-fixtu"

    @staticmethod
    def _base_commit() -> str:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "refs/remotes/origin/development"],
            text=True,
        ).strip()

    @classmethod
    def _changed_paths(cls) -> list[str]:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "diff", "--name-only", f"{cls._base_commit()}..{cls._candidate_ref()}"],
            text=True,
        ).splitlines()

    @classmethod
    def _bind(cls, **overrides):
        values = {
            "repo_root": ROOT,
            "candidate_ref": cls._candidate_ref(),
            "base_commit": cls._base_commit(),
            "changed_paths": cls._changed_paths(),
            "config_digest": "sha256:" + "a" * 64,
            "fixture_digest": "sha256:" + "b" * 64,
            "migration_digest": "sha256:" + "c" * 64,
        }
        values.update(overrides)
        return bind_preparatory_receipt(**values)

    def test_source_migration_manifest_matches_all_declared_bytes(self) -> None:
        result = validate_migration_manifest(ROOT)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["rows_checked"], len(MIGRATION_MANIFEST))
        self.assertTrue(all(row["status"] == "PASS" for row in result["rows"]))

    def test_local_fixture_is_loopback_and_non_live(self) -> None:
        config = json.loads((ROOT / "configs/pkt24/consumer.local-test.example.json").read_text())
        fixture = json.loads((PKT24 / "fixtures/local-gateway.json").read_text())
        result = validate_local_fixture(config, fixture)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertTrue(result["fixture_digest"].startswith("sha256:"))

    def test_live_mutation_is_rejected(self) -> None:
        config = json.loads((ROOT / "configs/pkt24/consumer.local-test.example.json").read_text())
        fixture = json.loads((PKT24 / "fixtures/local-gateway.json").read_text())
        mutated = copy.deepcopy(config)
        mutated["live_enabled"] = True
        result = validate_local_fixture(mutated, fixture)
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("live_enabled_must_be_false", result["errors"])

    def test_receipt_binds_exact_ref_and_stays_non_admitting(self) -> None:
        receipt = self._bind()
        self.assertEqual(receipt["status"], "PREPARATORY_ONLY")
        self.assertFalse(receipt["admission"]["admissible"])
        self.assertFalse(any(receipt["claims"].values()))
        self.assertEqual(validate_receipt(receipt), [])

    def test_receipt_claim_mutation_fails_digest_and_claim_guard(self) -> None:
        receipt = self._bind()
        receipt["claims"]["selectable"] = True
        errors = validate_receipt(receipt)
        self.assertIn("claim_must_be_false:selectable", errors)
        self.assertIn("receipt_digest_mismatch", errors)

    def test_receipt_rejects_base_or_changed_path_drift(self) -> None:
        with self.assertRaises(Pkt24RehearsalError):
            self._bind(base_commit="0" * 40)
        with self.assertRaises(Pkt24RehearsalError):
            self._bind(changed_paths=self._changed_paths()[:-1])
        with self.assertRaises(Pkt24RehearsalError):
            self._bind(changed_paths=self._changed_paths() + [self._changed_paths()[0]])

    def test_loopback_host_parsing_is_exact(self) -> None:
        config = json.loads((ROOT / "configs/pkt24/consumer.local-test.example.json").read_text())
        fixture = json.loads((PKT24 / "fixtures/local-gateway.json").read_text())
        valid_ipv6 = copy.deepcopy(config)
        valid_ipv6["gateway_url"] = "http://[::1]:8787/"
        self.assertEqual(validate_local_fixture(valid_ipv6, fixture)["status"], "PASS")
        for url in ("http://127.0.0.1.evil:8787", "http://127.0.0.1@evil:8787", "https://127.0.0.1:8787", "http://localhost:8787/path"):
            invalid = copy.deepcopy(config)
            invalid["gateway_url"] = url
            result = validate_local_fixture(invalid, fixture)
            self.assertEqual(result["status"], "HOLD", url)
            self.assertIn("gateway_url_must_be_loopback_http", result["errors"])

    def test_malformed_fixture_events_fail_closed(self) -> None:
        config = json.loads((ROOT / "configs/pkt24/consumer.local-test.example.json").read_text())
        fixture = json.loads((PKT24 / "fixtures/local-gateway.json").read_text())
        fixture["events"] = [{"event_id": "evt-1"}, {"event_id": "evt-1"}, "not-an-event"]
        result = validate_local_fixture(config, fixture)
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("fixture_events_must_have_stable_ids", result["errors"])

    def test_stage_reference_has_no_live_or_activation_claim(self) -> None:
        config = json.loads((ROOT / "configs/pkt24/consumer.stage.reference.json").read_text())
        self.assertEqual(config["mode"], "production")
        self.assertFalse(config["live_enabled"])
        self.assertFalse(config["activation_allowed"])
        self.assertIn("<platform-supplied", config["gateway_url"])


if __name__ == "__main__":
    unittest.main()
