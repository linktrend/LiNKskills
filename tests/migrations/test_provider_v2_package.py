"""Provider-v2 successor SQL is hash-bound and not applied from Skills."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "packages/persistence/MIGRATION-MANIFEST-PROVIDER-V2.json"
SQL = REPO / "supabase/migrations/20260915031801_lskills_provider_v2_runtime.sql"


class ProviderV2ManifestTests(unittest.TestCase):
    def test_digest_and_no_apply(self) -> None:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "source_only_no_apply")
        self.assertEqual(data["apply_authority"], "LiNKplatform")
        digest = hashlib.sha256(SQL.read_bytes()).hexdigest()
        self.assertEqual(data["entries"][0]["up_sha256"], digest)
        self.assertIn("provider_bindings", SQL.read_text(encoding="utf-8"))
        self.assertIn("enabled boolean not null default false", SQL.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
