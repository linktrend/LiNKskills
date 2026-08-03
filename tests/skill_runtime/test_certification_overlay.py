"""Tests for classification-ledger certification overlay + batch certifier gates."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(REPO_ROOT))

from lib.skill_runtime.catalog import build_catalog_index
from lib.skill_runtime.certification_overlay import (
    load_certification_overlay,
    overlay_from_ledger,
)


class CertificationOverlayTests(unittest.TestCase):
    def test_usable_without_sealed_evidence_falls_back_to_draft(self) -> None:
        overlay = overlay_from_ledger(
            {
                "skills": {
                    "canary-echo": {
                        "classification": "usable",
                        "sealed_live_receipt_evidence": [],
                    },
                    "git-safeguard": {
                        "classification": "draft",
                        "sealed_live_receipt_evidence": [],
                    },
                }
            }
        )
        self.assertEqual(overlay["canary-echo"], "draft")
        self.assertEqual(overlay["git-safeguard"], "draft")

    def test_usable_with_sealed_evidence_promotes(self) -> None:
        overlay = overlay_from_ledger(
            {
                "skills": {
                    "canary-echo": {
                        "classification": "usable",
                        "sealed_live_receipt_evidence": [
                            "evidence/phase10/sealed/canary-echo-sealed.json"
                        ],
                    }
                }
            }
        )
        self.assertEqual(overlay["canary-echo"], "usable")

    def test_build_catalog_applies_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "demo-skill"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: d\nversion: 0.1.0\n"
                "usage_trigger: t\nformat_profile: simple\n---\n# demo\n",
                encoding="utf-8",
            )
            (skill / "references" / "eval-suite.yaml").write_text(
                "skill_id: demo-skill\n", encoding="utf-8"
            )
            ledger_dir = root / "evidence" / "phase10"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "skill-classification-draft.json").write_text(
                json.dumps(
                    {
                        "skills": {
                            "demo-skill": {
                                "classification": "usable",
                                "sealed_live_receipt_evidence": [
                                    "evidence/phase10/sealed/demo.json"
                                ],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            overlay = load_certification_overlay(root)
            index = build_catalog_index(root, certification_overlay=overlay)
            self.assertEqual(index["skill_count"], 1)
            self.assertEqual(index["skills"][0]["certification_state"], "usable")


class CatalogCanarySkillTests(unittest.TestCase):
    def test_canary_echo_exists_with_executable_suite(self) -> None:
        skill = REPO_ROOT / "skills" / "canary-echo"
        suite = skill / "references" / "eval-suite.yaml"
        self.assertTrue(skill.is_dir())
        self.assertTrue(suite.is_file())
        text = suite.read_text(encoding="utf-8")
        self.assertIn("packaged_tool", text)
        self.assertIn("text-echo", text)
        self.assertIn("scenarios:", text)

    def test_repo_overlay_loader_does_not_invent_usable(self) -> None:
        # Before sealed certify lands, missing evidence must not yield usable.
        # After sealed certify, usable is allowed only with evidence paths.
        overlay = load_certification_overlay(REPO_ROOT)
        for skill_id, state in overlay.items():
            if state == "usable":
                ledger = json.loads(
                    (REPO_ROOT / "evidence/phase10/skill-classification-draft.json").read_text(
                        encoding="utf-8"
                    )
                )
                evidence = ledger["skills"][skill_id].get("sealed_live_receipt_evidence") or []
                self.assertTrue(evidence, msg=f"{skill_id} usable without evidence")


if __name__ == "__main__":
    unittest.main()
