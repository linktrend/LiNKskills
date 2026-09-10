#!/usr/bin/env python3
"""Structural checks for the production store readiness migration package."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "persistence"))

from linkskills_persistence.migration_package import (  # noqa: E402
    PACKAGE_ID,
    PAYLOAD_ENTRY_IDS,
    package_digest,
    payload_digest,
    verify_manifest_files,
)

MANIFEST = REPO_ROOT / "packages" / "persistence" / "MIGRATION-MANIFEST.json"
DOC = REPO_ROOT / "docs" / "migrations" / "MANIFEST-20260910-lskills-production-store-readiness.md"
BINDER = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260910_000013_lskills_production_store_readiness.sql"
)
BINDER_DOWN = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260910_000013_lskills_production_store_readiness_down.sql"
)

FORBIDDEN = (
    "security definer",
    "bypassrls true",
    "disable row level security",
    "force row level security",
    "grant all on",
    "to public",
    "to anon",
    "to authenticated",
    "password",
    "service_role key",
)


def _strip_sql_comments(sql: str) -> str:
    without_block = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    lines: list[str] = []
    for line in without_block.splitlines():
        if "--" in line:
            line = line.split("--", 1)[0]
        lines.append(line)
    return "\n".join(lines)


class ProductionStorePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.binder = BINDER.read_text(encoding="utf-8")
        cls.binder_code = _strip_sql_comments(cls.binder).lower()
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_files_exist(self) -> None:
        self.assertTrue(MANIFEST.is_file())
        self.assertTrue(DOC.is_file())
        self.assertTrue(BINDER.is_file())
        self.assertTrue(BINDER_DOWN.is_file())

    def test_manifest_identity_and_authority(self) -> None:
        data = self.manifest
        self.assertEqual(data["package_id"], PACKAGE_ID)
        self.assertEqual(data["status"], "source_only_no_apply")
        self.assertEqual(data["apply_authority"], "LiNKplatform")
        self.assertEqual(
            data["live_recovery_owner"],
            "01a0843c-0df9-74e2-907a-05c5f736d6ed",
        )
        self.assertEqual(data["compatible_postgres_major"], [17])
        self.assertEqual(len(data["entries"]), 12)
        self.assertEqual(
            [entry["id"] for entry in data["entries"][:-1]],
            list(PAYLOAD_ENTRY_IDS),
        )

    def test_on_disk_hashes_and_digests(self) -> None:
        verified = verify_manifest_files(REPO_ROOT, self.manifest)
        self.assertEqual(
            verified["payload_digest_sha256"],
            payload_digest(self.manifest),
        )
        self.assertEqual(
            verified["package_digest_sha256"],
            package_digest(self.manifest),
        )
        self.assertEqual(
            hashlib.sha256(BINDER.read_bytes()).hexdigest(),
            next(
                e["up_sha256"]
                for e in self.manifest["entries"]
                if e["id"] == "20260910_000013_lskills_production_store_readiness"
            ),
        )
        self.assertIn(self.manifest["payload_digest_sha256"], self.binder)

    def test_binder_is_additive_least_privilege(self) -> None:
        self.assertIn("create table if not exists lskills.store_package", self.binder_code)
        self.assertIn("security invoker", self.binder_code)
        self.assertIn("enable row level security", self.binder_code)
        self.assertIn("grant select on lskills.store_package", self.binder_code)
        self.assertNotIn("grant insert", self.binder_code)
        self.assertNotIn("drop schema", self.binder_code)
        self.assertNotIn("create role svc_lskills_runtime login", self.binder_code)
        for phrase in FORBIDDEN:
            self.assertNotIn(phrase, self.binder_code, phrase)

    def test_down_is_exact_object(self) -> None:
        down = BINDER_DOWN.read_text(encoding="utf-8")
        code = _strip_sql_comments(down).lower()
        self.assertIn("drop function if exists lskills.store_readiness_snapshot", code)
        self.assertIn("drop table if exists lskills.store_package", code)
        self.assertNotIn("drop schema", code)

    def test_handoff_doc_covers_platform_contract(self) -> None:
        self.assertIn("LiNKplatform alone", self.doc)
        self.assertIn("01a0843c-0df9-74e2-907a-05c5f736d6ed", self.doc)
        self.assertIn("PostgreSQL **17**", self.doc)
        self.assertIn("source_only_no_apply", self.doc)
        self.assertIn("BACKUP-RECEIPT-TEMPLATE.md", self.doc)


if __name__ == "__main__":
    unittest.main()
