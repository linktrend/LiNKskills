#!/usr/bin/env python3
"""Publisher bundle determinism and frontmatter migration tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "publisher"))

from linkskills_publisher.bundle import build_skill_bundle  # noqa: E402
from linkskills_publisher.migrate_frontmatter import migrate_dependencies  # noqa: E402


class BundleDeterminismTests(unittest.TestCase):
    def _write_skill(self, root: Path) -> Path:
        skill = root / "demo-skill"
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\n"
            "name: demo-skill\n"
            "description: demo\n"
            "version: 1.2.3\n"
            "---\n"
            "# demo-skill\n\nBody.\n",
            encoding="utf-8",
        )
        (skill / "references" / "eval-suite.yaml").write_text(
            "skill_id: demo-skill\npass_threshold: 0.8\nscenarios:\n  - id: a\n",
            encoding="utf-8",
        )
        (skill / "references" / "notes.md").write_text("notes\n", encoding="utf-8")
        return skill

    def test_same_input_same_hash_twice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = self._write_skill(Path(tmp))
            first = build_skill_bundle(skill)
            second = build_skill_bundle(skill)
            self.assertEqual(first["content_hash"], second["content_hash"])
            self.assertEqual(first["bundle_hash"], second["bundle_hash"])
            self.assertEqual(first["skill_id"], "demo-skill")
            self.assertEqual(first["version"], "1.2.3")
            self.assertTrue(first["content_hash"].startswith("sha256:"))
            self.assertTrue(first["eval_suite_hash"].startswith("sha256:"))
            self.assertGreaterEqual(len(first["fragments"]), 1)

    def test_corrupted_file_changes_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = self._write_skill(Path(tmp))
            before = build_skill_bundle(skill)
            target = skill / "SKILL.md"
            target.write_text(target.read_text(encoding="utf-8") + "\n# corrupted\n", encoding="utf-8")
            after = build_skill_bundle(skill)
            self.assertNotEqual(before["content_hash"], after["content_hash"])
            self.assertNotEqual(before["bundle_hash"], after["bundle_hash"])


class FrontmatterMigrationTests(unittest.TestCase):
    def test_maps_legacy_dependencies(self) -> None:
        deps = migrate_dependencies(
            {
                "dependencies": ["gws", "audit-protocol", "lib:style-guide"],
                "tools": ["read_file"],
                "permissions": ["fs_read", "api_access"],
                "engine": {"min_reasoning_tier": "balanced", "context_required": 64000},
            }
        )
        tool_ids = {t["id"] for t in deps["packaged_tools"]}
        self.assertIn("gws", tool_ids)
        self.assertIn("read_file", tool_ids)
        skill_ids = {s["id"] for s in deps["skill_dependencies"]}
        self.assertIn("audit-protocol", skill_ids)
        self.assertIn("filesystem_read", deps["host_capabilities"])
        self.assertIn("network", deps["host_capabilities"])
        self.assertTrue(any(r["key"] == "min_reasoning_tier" for r in deps["runtime_requirements"]))
        self.assertEqual(deps["library_assets"][0]["id"], "style-guide")


if __name__ == "__main__":
    unittest.main()
