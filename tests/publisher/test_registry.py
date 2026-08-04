#!/usr/bin/env python3
"""Publisher registry transactional release tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "publisher"))

from linkskills_publisher.registry import PublisherRegistry, publisher_db_path  # noqa: E402


class PublisherRegistryTests(unittest.TestCase):
    def _write_skill(self, root: Path) -> Path:
        skill = root / "demo-skill"
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: demo-skill\nversion: 2.0.0\ndescription: demo\n---\n# demo\n",
            encoding="utf-8",
        )
        (skill / "references" / "eval-suite.yaml").write_text(
            "skill_id: demo-skill\nscenarios: []\n",
            encoding="utf-8",
        )
        return skill

    def test_publish_release_is_transactional(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = self._write_skill(Path(tmp))
            registry = PublisherRegistry(publisher_db_path(Path(tmp) / "state"))
            published = registry.publish_release(skill, channel="internal", transactional=True)
            self.assertEqual(published.skill_id, "demo-skill")
            self.assertEqual(published.version, "2.0.0")
            loaded = registry.get_release("demo-skill", "2.0.0")
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.bundle_hash, published.bundle_hash)
            # Exact-content replay is idempotent.
            again = registry.publish_release(skill, channel="internal", transactional=True)
            self.assertEqual(again.bundle_hash, published.bundle_hash)
            registry.close()

    def test_publish_same_version_different_content_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._write_skill(root)
            registry = PublisherRegistry(publisher_db_path(root / "state"))
            registry.publish_release(skill, channel="internal", transactional=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo-skill\nversion: 2.0.0\ndescription: changed\n---\n# changed\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError) as ctx:
                registry.publish_release(skill, channel="internal", transactional=True)
            self.assertIn("immutable", str(ctx.exception).lower())
            registry.close()

    def test_backfill_from_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = PublisherRegistry(publisher_db_path(Path(tmp) / "state"))
            manifest = {
                "skill_id": "backfill",
                "version": "0.1.0",
                "bundle_hash": "sha256:abc",
                "content_hash": "sha256:def",
            }
            count = registry.backfill_from_manifests([manifest])
            self.assertEqual(count, 1)
            rows = registry.list_releases("backfill")
            self.assertEqual(len(rows), 1)
            registry.close()


if __name__ == "__main__":
    unittest.main()
