#!/usr/bin/env python3
"""Structural (no-DB) checks for gateway role RLS contract migration 000011.

These tests only read SQL and the migration manifest from disk.
They must never connect to a database or apply migrations.
"""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

UP = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260804_000011_lskills_gateway_role_rls_contract.sql"
)
DOWN = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260804_000011_lskills_gateway_role_rls_contract_down.sql"
)
MANIFEST = (
    REPO_ROOT
    / "docs"
    / "migrations"
    / "MANIFEST-20260804-lskills-gateway-role-rls-contract.md"
)
NOTE = REPO_ROOT / "docs" / "migrations" / "GATEWAY-ROLE-RLS-000011-NOTE.md"

SHA256_ROW_RE = re.compile(
    r"`(?P<path>supabase/migrations/[^`]+)`\s*\|\s*`(?P<sha>[0-9a-f]{64})`",
    re.IGNORECASE,
)

FORBIDDEN_UP = (
    "security definer",
    "bypassrls true",
    "alter role svc_lskills_gateway bypassrls",
    "alter role svc_lskills_runtime bypassrls",
    "disable row level security",
    "force row level security",
    "grant all on",
    "to public",
    "to anon",
    "to authenticated",
    "using (true)",
    "with check (true)",
    "1f2b1c21-11cd-4aaa-85ba-cb88adebc426",
    "8ac945ba-1604-44bb-8cd8-854e7d444034",
)


def _strip_sql_comments(sql: str) -> str:
    without_block = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    lines: list[str] = []
    for line in without_block.splitlines():
        if "--" in line:
            line = line.split("--", 1)[0]
        lines.append(line)
    return "\n".join(lines)


class GatewayRoleRlsContractPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.up_sql = UP.read_text(encoding="utf-8")
        cls.up_code = _strip_sql_comments(cls.up_sql).lower()
        cls.down_sql = DOWN.read_text(encoding="utf-8")
        cls.down_code = _strip_sql_comments(cls.down_sql).lower()
        cls.manifest_text = MANIFEST.read_text(encoding="utf-8")

    def test_package_files_exist(self) -> None:
        self.assertTrue(UP.is_file(), f"missing {UP}")
        self.assertTrue(DOWN.is_file(), f"missing {DOWN}")
        self.assertTrue(MANIFEST.is_file(), f"missing {MANIFEST}")
        self.assertTrue(NOTE.is_file(), f"missing {NOTE}")

    def test_manifest_sha256_pins_match_disk(self) -> None:
        pins = {m.group("path"): m.group("sha") for m in SHA256_ROW_RE.finditer(self.manifest_text)}
        self.assertIn(str(UP.relative_to(REPO_ROOT)), pins)
        self.assertIn(str(DOWN.relative_to(REPO_ROOT)), pins)
        for rel, expected in pins.items():
            path = REPO_ROOT / rel
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, expected, f"SHA-256 mismatch for {rel}")

    def test_additive_only_no_schema_drop(self) -> None:
        self.assertNotIn("drop schema", self.up_code)
        self.assertNotIn("drop schema", self.down_code)
        self.assertNotIn("truncate", self.up_code)
        self.assertNotIn("drop table", self.up_code)

    def test_forbidden_privilege_escape_hatches_absent(self) -> None:
        for needle in FORBIDDEN_UP:
            self.assertNotIn(needle, self.up_code, f"forbidden construct in up: {needle}")

    def test_grants_runtime_membership_to_gateway(self) -> None:
        self.assertIn("svc_lskills_gateway", self.up_sql)
        self.assertIn("grant svc_lskills_runtime to svc_lskills_gateway", self.up_code)
        self.assertIn("nologin", self.up_code)
        self.assertIn("nobypassrls", self.up_code)

    def test_gateway_events_policy_requires_actor_org(self) -> None:
        self.assertIn("lskills_gateway_events_runtime_all", self.up_sql)
        self.assertIn("lskills.org_matches(org_id)", self.up_code)
        self.assertIn("lskills.actor_matches(actor_id)", self.up_code)
        # Historical anonymous branch must not remain in the up migration body.
        self.assertNotIn("org_id is null and actor_id is null", self.up_code)

    def test_down_restores_null_branch_and_revokes_membership(self) -> None:
        self.assertIn("org_id is null and actor_id is null", self.down_code)
        self.assertIn("revoke svc_lskills_runtime from svc_lskills_gateway", self.down_code)
        self.assertNotIn("drop role svc_lskills_gateway", self.down_code)

    def test_platform_only_apply_authority_documented(self) -> None:
        combined = self.up_sql + self.manifest_text + NOTE.read_text(encoding="utf-8")
        self.assertTrue(
            any(p in combined for p in ("LiNKplatform alone", "Platform alone")),
            "missing Platform-only apply authority wording",
        )


if __name__ == "__main__":
    unittest.main()
