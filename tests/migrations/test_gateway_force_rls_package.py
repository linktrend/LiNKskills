#!/usr/bin/env python3
"""Structural (no-DB) checks for gateway FORCE RLS migration package 000011."""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FORCE_UP = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260803_000011_lskills_gateway_force_rls.sql"
)
FORCE_DOWN = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260803_000011_lskills_gateway_force_rls_down.sql"
)
MANIFEST = (
    REPO_ROOT
    / "docs"
    / "migrations"
    / "MANIFEST-20260803-lskills-gateway-force-rls.md"
)
NOTE = REPO_ROOT / "docs" / "migrations" / "GATEWAY-FORCE-RLS-000011-NOTE.md"

SHA256_ROW_RE = re.compile(
    r"`(?P<path>supabase/migrations/[^`]+)`\s*\|\s*`(?P<sha>[0-9a-f]{64})`",
    re.IGNORECASE,
)

FORCE_TABLES = (
    "idempotency",
    "side_effect_intents",
    "gateway_events",
    "skill_runs",
    "run_events",
    "feedback",
    "trace_to_eval_candidates",
)


def _strip_sql_comments(sql: str) -> str:
    without_block = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    lines: list[str] = []
    for line in without_block.splitlines():
        if "--" in line:
            line = line.split("--", 1)[0]
        lines.append(line)
    return "\n".join(lines)


class GatewayForceRlsPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.up_sql = FORCE_UP.read_text(encoding="utf-8")
        cls.up_code = _strip_sql_comments(cls.up_sql).lower()
        cls.down_sql = FORCE_DOWN.read_text(encoding="utf-8")
        cls.down_code = _strip_sql_comments(cls.down_sql).lower()
        cls.manifest_text = MANIFEST.read_text(encoding="utf-8")

    def test_files_exist(self) -> None:
        self.assertTrue(FORCE_UP.is_file())
        self.assertTrue(FORCE_DOWN.is_file())
        self.assertTrue(MANIFEST.is_file())
        self.assertTrue(NOTE.is_file())

    def test_additive_only_no_drop_schema_or_bypass(self) -> None:
        self.assertNotIn("drop schema", self.up_code)
        self.assertNotIn("drop schema", self.down_code)
        self.assertNotIn("bypassrls", self.up_code)
        self.assertNotIn("service_role", self.up_code)
        self.assertNotIn("disable row level security", self.up_code)

    def test_force_rls_on_gateway_tables(self) -> None:
        for table in FORCE_TABLES:
            self.assertIn(
                f"alter table lskills.{table} force row level security",
                self.up_code,
            )
            self.assertIn(
                f"alter table lskills.{table} no force row level security",
                self.down_code,
            )

    def test_platform_only_apply_authority(self) -> None:
        note = NOTE.read_text(encoding="utf-8")
        blob = self.manifest_text + "\n" + note + "\n" + self.up_sql
        self.assertTrue(
            any(p in blob for p in ("LiNKplatform alone", "Platform alone")),
            "000011 note/manifest must state Platform-only live apply",
        )

    def test_manifest_sha256_matches_sql_bytes(self) -> None:
        rows = {
            m.group("path"): m.group("sha")
            for m in SHA256_ROW_RE.finditer(self.manifest_text)
        }
        expected = {
            "supabase/migrations/20260803_000011_lskills_gateway_force_rls.sql": FORCE_UP,
            "supabase/migrations/20260803_000011_lskills_gateway_force_rls_down.sql": FORCE_DOWN,
        }
        for rel, path in expected.items():
            self.assertIn(rel, rows, f"missing manifest row for {rel}")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(
                rows[rel],
                actual,
                f"manifest SHA-256 mismatch for {rel}",
            )


if __name__ == "__main__":
    unittest.main()
