"""LR-WP-003 citation-enforcer method tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "citation-enforcer"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))
sys.path.insert(0, str(ROOT / "packages" / "core"))
from linkskills_contracts import validate_instance  # noqa: E402
from linkskills_core.hashing import verify_execution_profile_hashes  # noqa: E402


class CitationEnforcerMethodTests(unittest.TestCase):
    def test_profile_hashes(self) -> None:
        payload = json.loads((SKILL / "references" / "skill-pack.json").read_text(encoding="utf-8"))
        self.assertTrue(validate_instance(payload, "skill-pack").ok)
        self.assertEqual(verify_execution_profile_hashes(SKILL), [])

    def test_observed_absence_with_pointer_succeeds(self) -> None:
        payload = {
            "claims": [
                {
                    "claim_id": "c1",
                    "claim_text": "The figure is unpublished.",
                    "source_type": "file",
                    "source_pointers": ["notes/absence.md"],
                    "rel": "contradicts",
                    "evidence_class": "observed_absence",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "in.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SKILL / "scripts/helper_tool.py"), "--input", str(path)], capture_output=True, text=True, check=True)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "SUCCESS")
        self.assertEqual(output["citations"][0]["rel"], "contradicts")
        self.assertEqual(output["citations"][0]["negative_evidence"], "observed_absence")

    def test_missing_pointer_and_cycles_block(self) -> None:
        missing = {"claims": [{"claim_id": "c1", "claim_text": "Unsupported figure.", "source_type": "file"}]}
        cyclic = {
            "claims": [
                {"claim_id": "a", "claim_text": "A claim text", "source_pointers": ["a.md"], "source_type": "file"},
                {"claim_id": "b", "claim_text": "B claim text", "source_pointers": ["b.md"], "source_type": "file"},
            ],
            "claim_links": [
                {"claim_id": "a", "rel": "cites", "target_kind": "claim", "target_id": "b"},
                {"claim_id": "b", "rel": "cites", "target_kind": "claim", "target_id": "a"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "missing.json"
            cyclic_path = Path(tmp) / "cyclic.json"
            missing_path.write_text(json.dumps(missing), encoding="utf-8")
            cyclic_path.write_text(json.dumps(cyclic), encoding="utf-8")
            missing_result = subprocess.run([sys.executable, str(SKILL / "scripts/helper_tool.py"), "--input", str(missing_path)], capture_output=True, text=True)
            cyclic_result = subprocess.run([sys.executable, str(SKILL / "scripts/helper_tool.py"), "--input", str(cyclic_path)], capture_output=True, text=True)
        self.assertNotEqual(missing_result.returncode, 0)
        self.assertNotEqual(cyclic_result.returncode, 0)
        self.assertIn("acyclic", cyclic_result.stdout.lower())

    def test_eval_covers_negative_and_cycle_cases(self) -> None:
        suite = json.loads((SKILL / "references/eval-suite.json").read_text(encoding="utf-8"))
        ids = {case["case_id"] for case in suite["cases"]}
        self.assertIn("negative-evidence-versus-missing", ids)
        self.assertIn("cyclic-claim-link-must-block", ids)


if __name__ == "__main__":
    unittest.main()
