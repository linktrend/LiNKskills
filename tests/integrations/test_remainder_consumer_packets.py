"""Disabled remainder consumer bindings never grant permission-to-act."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INVENTORY = REPO / "configs/consumer-activation/remainder-consumer-inventory.json"
BINDINGS = REPO / "configs/consumer-activation/remainder-provider-bindings.template.json"
LIBRARIAN = REPO / "configs/librarian/install-contract.json"


class RemainderConsumerContractTests(unittest.TestCase):
    def test_inventory_is_disabled_and_does_not_invent_ids(self) -> None:
        data = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.assertTrue(data["disabledByDefault"])
        self.assertFalse(data["enabled"])
        self.assertFalse(data["skillRetrievalCreatesCapabilityGrants"])
        self.assertFalse(data["permissionToAct"])
        names = {row["id"] for row in data["consumers"]}
        self.assertEqual(
            names,
            {
                "openclaw-prime-lisa",
                "openclaw-prime-david",
                "openclaw-prime-eric",
                "openclaw-prime-sara",
                "openclaw-prime-jane",
                "linkautowork-ai-automations",
                "codex",
                "cursor",
            },
        )
        for row in data["consumers"]:
            self.assertFalse(row["paciProductionClientObserved"])
            self.assertNotIn("secret_ref", row)
            self.assertNotIn("organizationId", row)

    def test_bindings_default_disabled(self) -> None:
        data = json.loads(BINDINGS.read_text(encoding="utf-8"))
        self.assertFalse(data["enabled"])
        self.assertFalse(data["liveApply"])
        for row in data["bindings"]:
            self.assertFalse(row["enabled"])
            self.assertEqual(row["release_ids"], [])

    def test_librarian_install_is_supervised(self) -> None:
        data = json.loads(LIBRARIAN.read_text(encoding="utf-8"))
        self.assertEqual(data["workerVersion"], "0.2")
        self.assertTrue(data["supervisedFirst"])
        self.assertFalse(data["unsupervisedProduction"])
        self.assertTrue(data["host"]["doNotEditFromLiNKskills"])


if __name__ == "__main__":
    unittest.main()
