"""Contract tests for PKT-22 role-pack manifests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROLE_PACKS = ROOT / "role-packs"
MANIFESTS = sorted(ROLE_PACKS.glob("*.json"))
EXPECTED_ROLES = {"lisa-ceo", "eric-cto", "david-cpo", "sara-coo-cfo", "jane-chief-trading-officer"}
REFERENCE_ONLY = {"qualification-closure", "pkt-22-23-contradiction", "pkt-22-source-receipt"}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
OPAQUE_RE = re.compile(r"^opaque:[A-Za-z0-9][A-Za-z0-9._:/-]{1,158}$")


class RolePackManifestTests(unittest.TestCase):
    """Verify immutable, non-authoritative role-pack contracts."""

    def test_exactly_five_manifests_and_authoritative_shape(self) -> None:
        """All five planned manifests expose the v0.1 contract shape."""
        self.assertEqual({path.stem for path in MANIFESTS}, EXPECTED_ROLES | REFERENCE_ONLY)
        for path in MANIFESTS:
            if path.stem in REFERENCE_ONLY:
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "0.1")
            self.assertRegex(payload["version"], r"^1\.0\.0$")
            self.assertEqual(payload["activation"], {"enabled": False, "activation_owner": "consumer"})
            self.assertEqual(payload["trust_boundary"], "linkskills-role-pack")
            self.assertEqual(payload["compatibility"]["min_contract_version"], "0.2")
            self.assertTrue(payload["release_refs"])

    def test_exact_release_refs_and_qualification_receipts(self) -> None:
        """Every entry has an immutable artifact digest and opaque eligibility receipt."""
        for path in MANIFESTS:
            if path.stem in REFERENCE_ONLY:
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            for entry in payload["release_refs"]:
                self.assertRegex(entry["artifact_digest"], DIGEST_RE)
                self.assertRegex(entry["eligibility_ref"], OPAQUE_RE)
                self.assertTrue(entry.get("required", True))
            self.assertEqual(len(payload["release_refs"]), len({x["release_id"] for x in payload["release_refs"]}))

    def test_capability_applicability_and_runtime_profiles(self) -> None:
        """Role applicability and execution profiles are explicit for every pack."""
        expected = {
            "lisa-ceo": {"governance", "workforce", "incident"},
            "eric-cto": {"development", "architecture", "incident"},
            "david-cpo": {"product", "market", "launch"},
            "sara-coo-cfo": {"operations", "finance", "procurement"},
            "jane-chief-trading-officer": {"trading-operations", "risk-governance", "reporting"},
        }
        for path in MANIFESTS:
            if path.stem in REFERENCE_ONLY:
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(expected[payload["role_pack_id"]].issubset(payload["required_capability_classes"]))
            self.assertGreaterEqual(len(payload["compatibility"]["runtime_profiles"]), 2)
            self.assertEqual(payload["applicability"]["scope"], "program" if path.stem.startswith("jane-") else "organization")

    def test_no_authority_or_private_binding_fields(self) -> None:
        """Manifests cannot contain identity, credentials, activation, or private data."""
        forbidden = {"identity", "credential", "credentials", "private_data", "account_binding", "account", "live_pin", "skill_body"}
        for path in MANIFESTS:
            if path.stem in REFERENCE_ONLY:
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
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
            self.assertTrue(keys.isdisjoint(forbidden))
            self.assertFalse(payload.get("activation", {}).get("enabled", True))

    def test_negative_manual_trading_and_unknown_boundary(self) -> None:
        """Jane remains non-executing and every manifest has the fixed boundary."""
        jane = json.loads((ROLE_PACKS / "jane-chief-trading-officer.json").read_text(encoding="utf-8"))
        constraints = " ".join(jane["applicability"]["constraints"]).lower()
        self.assertIn("no manual-trade", constraints)
        self.assertIn("no orders", constraints)
        self.assertNotIn("manual-trade", " ".join(x["release_id"] for x in jane["release_refs"]))
        for path in MANIFESTS:
            if path.stem not in REFERENCE_ONLY:
                self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["trust_boundary"], "linkskills-role-pack")


if __name__ == "__main__":
    unittest.main()
