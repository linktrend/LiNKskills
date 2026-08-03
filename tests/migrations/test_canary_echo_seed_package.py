#!/usr/bin/env python3
"""Structural (no-DB) checks for the canary-echo usable seed migration package.

These tests only read SQL and the migration manifest from disk.
They must never connect to a database or apply migrations.
"""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SEED_UP = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260803_000010_lskills_canary_echo_usable_seed.sql"
)
SEED_DOWN = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260803_000010_lskills_canary_echo_usable_seed_down.sql"
)
MANIFEST = (
    REPO_ROOT
    / "docs"
    / "migrations"
    / "MANIFEST-20260803-lskills-canary-echo-usable-seed.md"
)
NOTE = REPO_ROOT / "docs" / "migrations" / "CANARY-ECHO-000010-NOTE.md"

SHA256_ROW_RE = re.compile(
    r"`(?P<path>supabase/migrations/[^`]+)`\s*\|\s*`(?P<sha>[0-9a-f]{64})`",
    re.IGNORECASE,
)

PLATFORM_ONLY_PHRASES = (
    "LiNKplatform alone",
    "Platform alone",
)


def _strip_sql_comments(sql: str) -> str:
    """Remove `--` line comments and `/* ... */` blocks for structural scans."""
    without_block = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    lines: list[str] = []
    for line in without_block.splitlines():
        if "--" in line:
            line = line.split("--", 1)[0]
        lines.append(line)
    return "\n".join(lines)


class CanaryEchoSeedPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.up_sql = SEED_UP.read_text(encoding="utf-8")
        cls.up_code = _strip_sql_comments(cls.up_sql).lower()
        cls.down_sql = SEED_DOWN.read_text(encoding="utf-8")
        cls.down_code = _strip_sql_comments(cls.down_sql).lower()
        cls.manifest_text = MANIFEST.read_text(encoding="utf-8")

    def test_seed_up_file_exists(self) -> None:
        self.assertTrue(SEED_UP.is_file(), f"missing {SEED_UP}")

    def test_seed_down_file_exists(self) -> None:
        self.assertTrue(SEED_DOWN.is_file(), f"missing {SEED_DOWN}")

    def test_manifest_and_note_exist(self) -> None:
        self.assertTrue(MANIFEST.is_file(), f"missing {MANIFEST}")
        self.assertTrue(NOTE.is_file(), f"missing {NOTE}")

    def test_additive_only_no_drop_schema(self) -> None:
        self.assertNotIn("drop schema", self.up_code)
        self.assertNotIn("drop schema", self.down_code)
        self.assertNotIn("truncate", self.up_code)

    def test_no_disable_usable_trigger(self) -> None:
        self.assertNotIn("disable trigger", self.up_code)
        self.assertNotIn("drop trigger", self.up_code)
        self.assertNotIn("enforce_usable_requires_passing_eval", self.up_code)

    def test_contains_canary_echo(self) -> None:
        self.assertIn("canary-echo", self.up_sql)
        self.assertIn("0.2.0", self.up_sql)
        self.assertIn("skills/canary-echo/references/eval-suite.yaml", self.up_sql)

    def test_eval_runs_insert_before_usable_update(self) -> None:
        eval_pos = self.up_code.find("insert into lskills.eval_runs")
        usable_pos = self.up_code.find("certification_state = 'usable'")
        self.assertGreaterEqual(eval_pos, 0, "missing eval_runs insert")
        self.assertGreaterEqual(usable_pos, 0, "missing usable update")
        self.assertLess(
            eval_pos,
            usable_pos,
            "passing eval_runs insert must appear before usable promotion",
        )
        draft_pos = self.up_code.find("'draft'")
        self.assertGreaterEqual(draft_pos, 0, "catalog insert should start as draft")
        self.assertLess(draft_pos, eval_pos)

    def test_eval_run_is_passing(self) -> None:
        self.assertRegex(
            self.up_code,
            r"insert\s+into\s+lskills\.eval_runs[\s\S]*?passed[\s\S]*?true",
        )
        self.assertIn("'high'", self.up_sql)

    def test_idempotent_on_conflict_patterns(self) -> None:
        self.assertIn("on conflict", self.up_code)
        self.assertIn("do nothing", self.up_code)

    def test_down_deletes_only_canary_echo_rows(self) -> None:
        self.assertIn("canary-echo", self.down_sql)
        self.assertIn("delete from lskills.catalog", self.down_code)
        self.assertIn("delete from lskills.eval_runs", self.down_code)
        self.assertNotIn("drop table", self.down_code)
        self.assertNotIn("drop schema", self.down_code)
        self.assertNotIn("cascade", self.down_code)

    def test_manifest_sha256_matches_sql_bytes(self) -> None:
        rows = {
            match.group("path"): match.group("sha")
            for match in SHA256_ROW_RE.finditer(self.manifest_text)
        }
        for relative, path in (
            (
                "supabase/migrations/20260803_000010_lskills_canary_echo_usable_seed.sql",
                SEED_UP,
            ),
            (
                "supabase/migrations/20260803_000010_lskills_canary_echo_usable_seed_down.sql",
                SEED_DOWN,
            ),
        ):
            self.assertIn(relative, rows, f"manifest missing SHA-256 row for {relative}")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(
                rows[relative],
                actual,
                f"manifest SHA-256 does not match on-disk bytes for {relative}",
            )

    def test_manifest_states_platform_only_live_apply(self) -> None:
        self.assertTrue(
            any(p in self.manifest_text for p in PLATFORM_ONLY_PHRASES),
            "manifest must state Platform-only live apply",
        )
        self.assertIn("applies live", self.manifest_text.lower())
        note = NOTE.read_text(encoding="utf-8")
        self.assertTrue(
            any(p in note for p in PLATFORM_ONLY_PHRASES),
            "000010 note must state Platform-only live apply",
        )

    def test_manifest_documents_verification_and_rollback(self) -> None:
        lower = self.manifest_text.lower()
        self.assertIn("verification sql", lower)
        self.assertIn("rollback", lower)
        self.assertIn("canary-echo", self.manifest_text)

    def test_does_not_rewrite_000003_seed(self) -> None:
        seed_003 = (
            REPO_ROOT
            / "supabase"
            / "migrations"
            / "20260715_000003_lskills_catalog_seed.sql"
        )
        text_003 = seed_003.read_text(encoding="utf-8")
        self.assertNotIn("canary-echo", text_003)
        self.assertIn("does not rewrite", self.up_sql.lower())
        self.assertIn("000003", self.up_sql)

if __name__ == "__main__":
    unittest.main()
