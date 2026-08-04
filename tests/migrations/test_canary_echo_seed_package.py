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

    def test_fail_closed_assertions_not_silent_do_nothing(self) -> None:
        """Up must assert pinned row equality; silent DO NOTHING promote is forbidden."""
        self.assertIn("raise exception", self.up_code)
        self.assertIn("fail-closed", self.up_code)
        # Centralized package UUID pins must remain present for parent hash refresh.
        for pin in (
            "c4e00010-a001-4000-8000-c4a47ee00001",
            "c4e00010-a002-4000-8000-c4a47ee00001",
            "c4e00010-a003-4000-8000-c4a47ee00001",
            "c4e00010-a004-4000-8000-c4a47ee00001",
        ):
            self.assertIn(pin, self.up_sql)
        # Broad silent conflict swallow without equality check is not acceptable.
        # Prefer check-then-insert / equality assert over bare DO NOTHING promote.
        self.assertNotRegex(
            self.up_code,
            r"on\s+conflict\s*\([^)]+\)\s*do\s+nothing",
            "use fail-closed equality checks instead of silent ON CONFLICT DO NOTHING",
        )

    def test_down_deletes_only_exact_package_ids_and_hashes(self) -> None:
        self.assertIn("canary-echo", self.down_sql)
        self.assertIn("delete from lskills.catalog", self.down_code)
        self.assertIn("delete from lskills.eval_runs", self.down_code)
        self.assertNotIn("drop table", self.down_code)
        self.assertNotIn("drop schema", self.down_code)
        self.assertNotIn("cascade", self.down_code)
        # Exact package UUID guards (no broad skill_id+version wipe).
        for pin in (
            "c4e00010-a001-4000-8000-c4a47ee00001",
            "c4e00010-a002-4000-8000-c4a47ee00001",
            "c4e00010-a003-4000-8000-c4a47ee00001",
            "c4e00010-a004-4000-8000-c4a47ee00001",
        ):
            self.assertIn(pin, self.down_sql)
        self.assertIn(
            "skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb",
            self.down_sql,
        )
        self.assertIn(
            "a0bb2d56703cb95a6766a8902176f613dffed6af39d798546b338c5b3d77c262",
            self.down_sql,
        )
        # Forbid unscoped skill/version deletes without ID/hash guards.
        self.assertNotRegex(
            self.down_code,
            r"delete\s+from\s+lskills\.catalog\s+where\s+skill_id\s*=\s*'canary-echo'\s+"
            r"and\s+version\s*=\s*'0\.2\.0'\s*;",
        )
        self.assertNotRegex(
            self.down_code,
            r"delete\s+from\s+lskills\.releases\s+where\s+skill_id\s*=\s*'canary-echo'\s+"
            r"and\s+version\s*=\s*'0\.2\.0'\s*;",
        )
        self.assertNotRegex(
            self.down_code,
            r"delete\s+from\s+lskills\.eval_runs\s+where\s+skill_id\s*=\s*'canary-echo'\s+"
            r"and\s+skill_version\s*=\s*'0\.2\.0'\s*;",
        )

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
