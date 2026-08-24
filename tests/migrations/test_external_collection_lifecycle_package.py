#!/usr/bin/env python3
"""Read-only structural checks for the PKT-03 migration package."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
UP = REPO_ROOT / "supabase/migrations/20260824_000012_lskills_external_collection_lifecycle.sql"
DOWN = REPO_ROOT / "supabase/migrations/20260824_000012_lskills_external_collection_lifecycle_down.sql"
MANIFEST = REPO_ROOT / "packages/persistence/MIGRATION-MANIFEST.json"


class ExternalCollectionMigrationPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = UP.read_text(encoding="utf-8")
        cls.code = cls.sql.lower()
        cls.compact_code = " ".join(cls.code.split())
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_source_only_and_hashes_both_directions(self):
        self.assertEqual(self.manifest["status"], "source_only_no_apply")
        entry = self.manifest["entries"][0]
        self.assertEqual(entry["apply_authority"], "LiNKplatform")
        self.assertEqual(entry["up_sha256"], hashlib.sha256(UP.read_bytes()).hexdigest())
        self.assertEqual(entry["down_sha256"], hashlib.sha256(DOWN.read_bytes()).hexdigest())

    def test_up_migration_is_additive_and_has_lifecycle_tables(self):
        self.assertNotIn("drop table", self.code)
        self.assertNotIn("truncate", self.code)
        for table in (
            "external_vendor_releases", "external_collection_manifests",
            "external_adapted_releases", "external_update_candidates",
            "external_librarian_reviews", "external_current_pointers",
            "external_platform_receipts",
        ):
            self.assertIn(f"create table if not exists lskills.{table}", self.code)
        self.assertIn("idempotency_key text not null unique", self.code)
        self.assertIn("authority = 'linkplatform'", self.code)

    def test_no_independent_live_apply_is_documented(self):
        self.assertIn("platform review/apply receipts are required", self.code)
        self.assertIn("candidate arrival never changes", self.code)
        self.assertIn("grant select, insert on lskills.external_vendor_releases, lskills.external_collection_manifests, lskills.external_adapted_releases to svc_lskills_librarian", self.compact_code)
        self.assertIn("grant select, insert, update on lskills.external_update_candidates, lskills.external_librarian_reviews to svc_lskills_librarian", self.compact_code)

    def test_down_is_separate_exact_object_rollback(self):
        down = DOWN.read_text(encoding="utf-8").lower()
        self.assertIn("migrate:down", down)
        self.assertIn("exact additive objects", down)
        self.assertNotIn("drop schema", down)


if __name__ == "__main__":
    unittest.main()
