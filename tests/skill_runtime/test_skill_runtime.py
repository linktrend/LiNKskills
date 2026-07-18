#!/usr/bin/env python3
"""Unit tests for lib/skill_runtime (catalog, loader, telemetry buffer)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from lib.skill_runtime.catalog import build_catalog_index, list_skills, write_catalog_index
from lib.skill_runtime.loader import load_skill, resolve_skill_path
from lib.skill_runtime.telemetry import InvocationEvent, append_local_ledger, record_invocation


class CatalogTests(unittest.TestCase):
    def test_build_index_includes_all_skills(self) -> None:
        index = build_catalog_index(REPO_ROOT)
        self.assertGreaterEqual(index["skill_count"], 34)
        ids = {s["skill_id"] for s in index["skills"]}
        self.assertIn("git-safeguard", ids)
        self.assertIn("skill-template", ids)

    def test_write_and_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Minimal fake skill tree
            skill = root / "skills" / "demo-skill"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: demo\nversion: 1.0.0\n"
                "usage_trigger: demo\nformat_profile: simple\n---\n# demo\n",
                encoding="utf-8",
            )
            (skill / "references" / "eval-suite.yaml").write_text(
                "skill_id: demo-skill\npass_threshold: 0.8\nrubric:\n  - dimension: x\n"
                "scenarios:\n  - id: a\n",
                encoding="utf-8",
            )
            index = build_catalog_index(root)
            write_catalog_index(root, index)
            loaded = list_skills(index)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].skill_id, "demo-skill")
            self.assertEqual(loaded[0].certification_state, "draft")


class LoaderTests(unittest.TestCase):
    def test_resolve_and_load_git_safeguard(self) -> None:
        path = resolve_skill_path("git-safeguard", REPO_ROOT)
        self.assertTrue((path / "SKILL.md").is_file())
        bundle = load_skill("git-safeguard", repo_root=REPO_ROOT, require_usable=False)
        self.assertEqual(bundle.skill_id, "git-safeguard")
        self.assertTrue(bundle.eval_suite.is_file())
        self.assertIn("SKILL.md", bundle.disclosure_paths)

    def test_require_usable_blocks_draft(self) -> None:
        with self.assertRaises(PermissionError):
            load_skill("git-safeguard", repo_root=REPO_ROOT, require_usable=True)


class TelemetryTests(unittest.TestCase):
    def test_local_record_without_supabase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / "execution_ledger.jsonl"
            event = InvocationEvent(
                skill="git-safeguard",
                status="completed",
                summary="test invocation",
                task_id="20260718-1700-GITSAFE-000001",
                skill_version="1.1.0",
                agent_id="unit-test",
                program_ref="lskills",
            )
            result = record_invocation(
                event,
                repo_root=root,
                ledger_path=ledger,
                write_supabase=False,
            )
            self.assertTrue(result["local"])
            self.assertEqual(result["supabase"], "skipped")
            lines = ledger.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertEqual(payload["skill"], "git-safeguard")
            self.assertEqual(payload["event_id"], event.event_id)
            self.assertEqual(payload["program_ref"], "lskills")

    def test_append_local_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            event = InvocationEvent(
                skill="x",
                status="failed",
                summary="boom",
                task_id="20260718-1700-X-000001",
            )
            append_local_ledger(event, path)
            self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
