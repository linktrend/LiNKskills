from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from logic_engine.registry import build_registry_snapshot  # noqa: E402


class RegistryExtractionTests(unittest.TestCase):
    def test_registry_deterministic_ids_and_hashes(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        manifest_path = repo_root / "manifest.json"
        packages_path = Path(__file__).resolve().parents[1] / "config" / "packages.json"

        first = build_registry_snapshot(repo_root, manifest_path, packages_path).snapshot
        second = build_registry_snapshot(repo_root, manifest_path, packages_path).snapshot

        first_fingerprint = sorted(
            (item.capability_id, item.version, item.source_trace.source_path_hash)
            for item in first.capabilities
        )
        second_fingerprint = sorted(
            (item.capability_id, item.version, item.source_trace.source_path_hash)
            for item in second.capabilities
        )

        self.assertEqual(first.manifest_entries, len(first.capabilities))
        self.assertEqual(first_fingerprint, second_fingerprint)

    def test_v1_capabilities_present(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        manifest_path = repo_root / "manifest.json"
        packages_path = Path(__file__).resolve().parents[1] / "config" / "packages.json"
        snapshot = build_registry_snapshot(repo_root, manifest_path, packages_path).snapshot

        ids = {item.capability_id for item in snapshot.capabilities}
        self.assertIn("lead-engineer", ids)
        self.assertIn("persistent-qa", ids)
        self.assertIn("market-analyst", ids)
        self.assertIn("marketing-strategist", ids)


if __name__ == "__main__":
    unittest.main()
