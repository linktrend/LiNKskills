#!/usr/bin/env python3
"""Regression: tool source_hash must ignore runtime/tmp/cache noise."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "tool_runtime"))

from linkskills_tool_runtime.descriptor import (  # noqa: E402
    hash_tool_source_tree,
    iter_governed_source_files,
    load_tool_descriptor,
)


def _seed_minimal_tool(root: Path) -> None:
    """Write a minimal governed tool package under ``root``."""
    (root / "bin").mkdir(parents=True, exist_ok=True)
    (root / "bin" / "echo.py").write_text("print('ok')\n", encoding="utf-8")
    (root / "descriptor.yaml").write_text(
        "\n".join(
            [
                "tool_id: hash-demo",
                'version: "1.0.0"',
                "description: hash reproducibility fixture",
                "side_effect_class: none",
                "lifecycle_state: draft",
                "entrypoint:",
                "  transport: cli",
                "  command: python3",
                "  args:",
                "    - bin/echo.py",
                "platforms:",
                "  - any",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "README.md").write_text("# hash-demo\n", encoding="utf-8")


class SourceHashReproducibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="source-hash-")
        self.tool_dir = Path(self._tmpdir.name) / "hash-demo"
        self.tool_dir.mkdir()
        _seed_minimal_tool(self.tool_dir)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_ignored_tmp_and_cache_do_not_change_source_hash(self) -> None:
        clean = hash_tool_source_tree(self.tool_dir)

        tmp_dir = self.tool_dir / "tmp"
        tmp_dir.mkdir()
        (tmp_dir / "fs-allowlist.sb").write_text("(version 1)\n", encoding="utf-8")
        (tmp_dir / "scratch.bin").write_bytes(b"\x00\x01runtime-noise")

        cache = self.tool_dir / "__pycache__"
        cache.mkdir()
        (cache / "echo.cpython-312.pyc").write_bytes(b"bytecode-noise")

        (self.tool_dir / "bin" / "__pycache__").mkdir()
        (self.tool_dir / "bin" / "__pycache__" / "x.pyc").write_bytes(b"more")

        pytest_cache = self.tool_dir / ".pytest_cache"
        pytest_cache.mkdir()
        (pytest_cache / "v").write_text("cache", encoding="utf-8")

        dirty = hash_tool_source_tree(self.tool_dir)
        self.assertEqual(clean, dirty)

        descriptor = load_tool_descriptor(self.tool_dir)
        self.assertEqual(descriptor.source_hash, clean)

    def test_modifying_tracked_tool_code_changes_source_hash(self) -> None:
        before = hash_tool_source_tree(self.tool_dir)
        (self.tool_dir / "bin" / "echo.py").write_text("print('changed')\n", encoding="utf-8")
        after_bin = hash_tool_source_tree(self.tool_dir)
        self.assertNotEqual(before, after_bin)

        (self.tool_dir / "descriptor.yaml").write_text(
            (self.tool_dir / "descriptor.yaml").read_text(encoding="utf-8")
            + "timeout_seconds: 9\n",
            encoding="utf-8",
        )
        after_descriptor = hash_tool_source_tree(self.tool_dir)
        self.assertNotEqual(after_bin, after_descriptor)

    def test_dirty_tree_hash_matches_clean_allowlisted_copy(self) -> None:
        """Allowlisted hash of a dirty tree equals hashing a clean archive of the same sources."""
        (self.tool_dir / "tmp").mkdir()
        (self.tool_dir / "tmp" / "fs-allowlist.sb").write_text("noise\n", encoding="utf-8")
        (self.tool_dir / "__pycache__").mkdir()
        (self.tool_dir / "__pycache__" / "x.pyc").write_bytes(b"pyc")

        dirty_hash = hash_tool_source_tree(self.tool_dir)
        base = self.tool_dir.resolve()
        governed = list(iter_governed_source_files(self.tool_dir))
        self.assertTrue(governed)
        governed_rels = [p.relative_to(base).as_posix() for p in governed]
        self.assertFalse(any(rel == "tmp" or rel.startswith("tmp/") for rel in governed_rels))
        self.assertFalse(any("__pycache__" in rel.split("/") for rel in governed_rels))

        with tempfile.TemporaryDirectory(prefix="source-hash-clean-") as clean_home:
            clean_root = Path(clean_home) / "hash-demo"
            clean_root.mkdir()
            for src in governed:
                rel = src.relative_to(base)
                dest = clean_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            clean_hash = hash_tool_source_tree(clean_root)

        self.assertEqual(dirty_hash, clean_hash)

    def test_text_echo_package_excludes_gitignored_tmp(self) -> None:
        text_echo = REPO_ROOT / "tools" / "text-echo"
        if not text_echo.is_dir():
            self.skipTest("tools/text-echo missing")
        governed_rels = [
            p.relative_to(text_echo).as_posix()
            for p in iter_governed_source_files(text_echo)
        ]
        self.assertNotIn("tmp/fs-allowlist.sb", governed_rels)
        self.assertIn("descriptor.yaml", governed_rels)
        self.assertIn("bin/text-echo.py", governed_rels)


if __name__ == "__main__":
    unittest.main()
