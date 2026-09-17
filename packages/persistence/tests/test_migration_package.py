"""Manifest fingerprint verification for the production store package."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from linkskills_persistence.migration_package import (
    load_manifest,
    package_digest,
    payload_digest,
    verify_manifest_files,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


class MigrationPackageVerifyTests(unittest.TestCase):
    def test_admitted_manifest_verifies(self) -> None:
        manifest = load_manifest(REPO_ROOT)
        verified = verify_manifest_files(REPO_ROOT, manifest)
        self.assertEqual(verified["payload_digest_sha256"], payload_digest(manifest))
        self.assertEqual(verified["package_digest_sha256"], package_digest(manifest))
        self.assertEqual(manifest["package_digest_sha256"], verified["package_digest_sha256"])

    def test_tampered_hash_fails_closed(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / "packages/persistence/MIGRATION-MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )
        manifest["entries"][0]["up_sha256"] = "0" * 64
        with self.assertRaises(ValueError) as ctx:
            verify_manifest_files(REPO_ROOT, manifest)
        self.assertIn("migration_fingerprint_mismatch", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
