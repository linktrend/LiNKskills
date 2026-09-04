"""LR-WP-003 search-strategy one-way facade tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "search-strategy"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))
sys.path.insert(0, str(ROOT / "packages" / "core"))
from linkskills_contracts import validate_instance  # noqa: E402
from linkskills_core.hashing import verify_execution_profile_hashes  # noqa: E402


class SearchStrategyFacadeTests(unittest.TestCase):
    def test_profile_hashes(self) -> None:
        payload = json.loads((SKILL / "references" / "skill-pack.json").read_text(encoding="utf-8"))
        self.assertTrue(validate_instance(payload, "skill-pack").ok)
        self.assertEqual(payload["dependencies"]["skill_dependencies"], ["research"])
        self.assertEqual(verify_execution_profile_hashes(SKILL), [])

    def test_facade_routes_new_broad_workflow_to_research(self) -> None:
        payload = {"requested_skill": "search-strategy", "new_broad_workflow": True, "question": "What is the current official limit?"}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "in.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SKILL / "scripts/helper_tool.py"), "--input", str(path)], capture_output=True, text=True, check=True)
        output = json.loads(result.stdout)
        self.assertEqual(output["selected_skill"], "research")
        self.assertEqual(output["outcome"], "supersession")
        self.assertEqual(output["direction"], "one-way")
        self.assertFalse(output["legacy_skill_rewritten"])
        self.assertEqual(output["external_calls"], [])

    def test_legacy_router_flag_fails(self) -> None:
        payload = {"question": "Need current pricing data please", "use_legacy_router": True, "confidence_threshold": 0.8, "max_cost_tier": "web"}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "in.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SKILL / "scripts/helper_tool.py"), "--input", str(path)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_skill_text_excludes_router_and_named_providers(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("one-way facade", text)
        self.assertIn("tools/research", text)
        self.assertNotRegex(text, r"\bexa\b")
        self.assertIn("dependencies: [research]", (SKILL / "SKILL.md").read_text(encoding="utf-8"))

    def test_eval_covers_facade(self) -> None:
        suite = json.loads((SKILL / "references/eval-suite.json").read_text(encoding="utf-8"))
        ids = {case["case_id"] for case in suite["cases"]}
        self.assertIn("new-broad-workflow-facade-to-research", ids)
        blob = json.dumps(suite).lower()
        self.assertNotRegex(blob, r"\bexa\b")


if __name__ == "__main__":
    unittest.main()
