#!/usr/bin/env python3
"""Catalog discovery for packaged installs vs source-tree parents[3]."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATHS = [
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "tool_runtime",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
]
for path in PACKAGE_PATHS:
    sys.path.insert(0, str(path))

from linkskills_gateway.service import (  # noqa: E402
    REPO_ROOT_ENV,
    SkillsGatewayService,
    resolve_repo_root,
)


def _write_image_catalog(image_root: Path) -> None:
    catalog = image_root / "catalog"
    catalog.mkdir(parents=True)
    (catalog / "index.json").write_text(
        json.dumps(
            {
                "skills": [
                    {
                        "skill_id": "image-catalog-skill",
                        "version": "1.0.0",
                        "description": "catalog copied into the Server 01 image",
                        "certification_state": "usable",
                        "format_profile": "heavy",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


class PackagedRepoRootDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous = os.environ.get(REPO_ROOT_ENV)
        os.environ.pop(REPO_ROOT_ENV, None)

    def tearDown(self) -> None:
        if self._previous is None:
            os.environ.pop(REPO_ROOT_ENV, None)
        else:
            os.environ[REPO_ROOT_ENV] = self._previous

    def test_site_packages_parents_do_not_contain_image_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            installed = (
                base
                / "usr"
                / "local"
                / "lib"
                / "python3.11"
                / "site-packages"
                / "linkskills_gateway"
                / "service.py"
            )
            installed.parent.mkdir(parents=True)
            installed.write_text("# packaged module\n", encoding="utf-8")
            image_root = base / "opt" / "linkskills"
            _write_image_catalog(image_root)
            derived = installed.resolve().parents[3]
            self.assertEqual(derived, (base / "usr" / "local" / "lib").resolve())
            self.assertFalse((derived / "catalog" / "index.json").is_file())
            self.assertTrue((image_root / "catalog" / "index.json").is_file())

    def test_supported_repo_root_env_loads_packaged_image_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_root = Path(tmp) / "opt" / "linkskills"
            _write_image_catalog(image_root)
            os.environ[REPO_ROOT_ENV] = str(image_root)
            resolved = resolve_repo_root()
            self.assertEqual(resolved, image_root.resolve())
            service = SkillsGatewayService()
            self.assertEqual(service.repo_root, image_root.resolve())
            self.assertIn("image-catalog-skill", service._skills)
            ready = service.ready(auth_configured=True, auth_mode="local-test")
            self.assertTrue(ready["catalog_loaded"])
            self.assertEqual(ready["skill_count"], 1)

    def test_explicit_factory_repo_root_wins_over_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_root = Path(tmp) / "env-root"
            factory_root = Path(tmp) / "factory-root"
            _write_image_catalog(env_root)
            _write_image_catalog(factory_root)
            marker = factory_root / "catalog" / "index.json"
            payload = json.loads(marker.read_text(encoding="utf-8"))
            payload["skills"][0]["skill_id"] = "factory-catalog-skill"
            marker.write_text(json.dumps(payload), encoding="utf-8")
            os.environ[REPO_ROOT_ENV] = str(env_root)
            service = SkillsGatewayService(repo_root=factory_root)
            self.assertIn("factory-catalog-skill", service._skills)
            self.assertNotIn("image-catalog-skill", service._skills)


if __name__ == "__main__":
    unittest.main()
