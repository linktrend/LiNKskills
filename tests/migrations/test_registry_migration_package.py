#!/usr/bin/env python3
"""Structural (no-DB) checks for the lskills registry migration package.

These tests only read SQL and the migration manifest from disk.
They must never connect to a database or apply migrations.
"""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REGISTRY_SQL = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260727_000005_lskills_registry_foundation.sql"
)
CATALOG_CORE_SQL = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260715_000002_lskills_catalog_core.sql"
)
MANIFEST = (
    REPO_ROOT / "docs" / "migrations" / "MANIFEST-20260727-lskills-registry-v0.1.md"
)

REGISTRY_TABLES = (
    "releases",
    "bundles",
    "fragments",
    "tools",
    "execution_profiles",
    "certifications",
    "skill_runs",
    "run_events",
    "feedback",
    "trace_to_eval_candidates",
)

CATALOG_CORE_TABLES = ("catalog", "telemetry", "eval_runs")

SVC_ROLES = (
    "svc_lskills_runtime",
    "svc_lskills_librarian",
    "svc_observer",
)

SHA256_ROW_RE = re.compile(
    r"`(?P<path>supabase/migrations/[^`]+)`\s*\|\s*`(?P<sha>[0-9a-f]{64})`",
    re.IGNORECASE,
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


def _comment_lines(sql: str) -> list[str]:
    """Return `--` comment line bodies (text after `--`)."""
    bodies: list[str] = []
    for line in sql.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            bodies.append(stripped[2:].strip())
    return bodies


class RegistryMigrationPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry_sql = REGISTRY_SQL.read_text(encoding="utf-8")
        cls.registry_sql_lower = cls.registry_sql.lower()
        cls.registry_code = _strip_sql_comments(cls.registry_sql).lower()
        cls.manifest_text = MANIFEST.read_text(encoding="utf-8")

    def test_registry_migration_file_exists(self) -> None:
        self.assertTrue(REGISTRY_SQL.is_file(), f"missing {REGISTRY_SQL}")

    def test_additive_only_create_table_if_not_exists(self) -> None:
        self.assertIn("create table if not exists", self.registry_code)

    def test_no_drop_schema(self) -> None:
        self.assertNotIn("drop schema", self.registry_code)
        # Also forbid the phrase anywhere outside down-migration guidance comments.
        for body in _comment_lines(self.registry_sql):
            if "drop schema" in body.lower() and "down" not in body.lower():
                self.fail(f"unexpected drop schema guidance in comment: {body!r}")

    def test_no_executable_drop_table(self) -> None:
        self.assertNotIn("drop table", self.registry_code)
        for body in _comment_lines(self.registry_sql):
            lower = body.lower()
            if "drop table" not in lower:
                continue
            if "down" not in lower and "down-migration" not in self.registry_sql_lower:
                self.fail(
                    "drop table appears in a comment that is not down-migration guidance: "
                    f"{body!r}"
                )

    def test_no_truncate(self) -> None:
        self.assertNotIn("truncate", self.registry_code)

    def test_expected_registry_tables_declared(self) -> None:
        for table in REGISTRY_TABLES:
            needle = f"create table if not exists lskills.{table}"
            self.assertIn(
                needle,
                self.registry_code,
                f"missing additive create for lskills.{table}",
            )

    def test_rls_enabled_for_registry_tables(self) -> None:
        for table in REGISTRY_TABLES:
            needle = f"alter table lskills.{table} enable row level security"
            self.assertIn(needle, self.registry_code, f"RLS not enabled for {table}")

    def test_policies_for_runtime_librarian_observer(self) -> None:
        for role in SVC_ROLES:
            self.assertRegex(
                self.registry_code,
                rf"create\s+policy\b[\s\S]*?\bto\s+{re.escape(role)}\b",
                f"missing create policy targeting {role}",
            )
        # Spot-check that each expected table has at least one policy.
        for table in REGISTRY_TABLES:
            self.assertRegex(
                self.registry_code,
                rf"create\s+policy\s+\S+\s+on\s+lskills\.{re.escape(table)}\b",
                f"missing create policy on lskills.{table}",
            )

    def test_grants_mention_service_or_svc_roles(self) -> None:
        grant_blob = "\n".join(
            line for line in self.registry_code.splitlines() if "grant " in line
        )
        self.assertTrue(grant_blob.strip(), "expected grant statements in migration")
        mentions_service_role = "service_role" in grant_blob
        mentions_svc = any(role in grant_blob for role in SVC_ROLES)
        self.assertTrue(
            mentions_service_role or mentions_svc,
            "grants must mention service_role or named svc_* roles as authored",
        )
        # This package authors named svc roles (not service_role).
        for role in SVC_ROLES:
            self.assertIn(role, grant_blob, f"expected grant to {role}")

    def test_manifest_sha256_matches_registry_sql_bytes(self) -> None:
        self.assertTrue(MANIFEST.is_file(), f"missing {MANIFEST}")
        rows = {
            match.group("path"): match.group("sha")
            for match in SHA256_ROW_RE.finditer(self.manifest_text)
        }
        relative = "supabase/migrations/20260727_000005_lskills_registry_foundation.sql"
        self.assertIn(relative, rows, "manifest missing SHA-256 row for registry SQL")
        actual = hashlib.sha256(REGISTRY_SQL.read_bytes()).hexdigest()
        self.assertEqual(
            rows[relative],
            actual,
            "manifest SHA-256 does not match hashlib.sha256 of registry SQL bytes",
        )

    def test_manifest_prerequisite_migration_files_exist(self) -> None:
        rows = list(SHA256_ROW_RE.finditer(self.manifest_text))
        self.assertGreaterEqual(len(rows), 2, "manifest should list prerequisites + package")
        for match in rows:
            rel = match.group("path")
            path = REPO_ROOT / rel
            self.assertTrue(path.is_file(), f"manifest references missing file: {rel}")
            expected_sha = match.group("sha")
            actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(
                expected_sha,
                actual_sha,
                f"manifest SHA-256 mismatch for {rel}",
            )


class CatalogCoreRlsStructuralTests(unittest.TestCase):
    """Read-only companion checks for prior catalog_core RLS patterns."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = CATALOG_CORE_SQL.read_text(encoding="utf-8")
        cls.code = _strip_sql_comments(cls.sql).lower()

    def test_catalog_core_file_exists(self) -> None:
        self.assertTrue(CATALOG_CORE_SQL.is_file(), f"missing {CATALOG_CORE_SQL}")

    def test_catalog_telemetry_eval_runs_enable_rls(self) -> None:
        self.assertIn("enable row level security", self.code)
        for table in CATALOG_CORE_TABLES:
            needle = f"alter table lskills.{table} enable row level security"
            self.assertIn(
                needle,
                self.code,
                f"catalog_core missing RLS enable for lskills.{table}",
            )


if __name__ == "__main__":
    unittest.main()
