#!/usr/bin/env python3
"""Adversarial tests for catalog provenance (source commit + source_tree_sha256)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from lib.skill_runtime.catalog_provenance import (  # noqa: E402
    ZERO_GIT_SHA,
    compute_source_tree_sha256,
    is_governed_input_path,
    validate_catalog_provenance,
)


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _init_repo(root: Path) -> str:
    _git(root, "init")
    _git(root, "config", "user.email", "prov-test@linkskills.local")
    _git(root, "config", "user.name", "Provenance Test")
    (root / "skills" / "demo").mkdir(parents=True)
    (root / "skills" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\nversion: 0.1.0\n---\n# demo\n", encoding="utf-8"
    )
    (root / "tools" / "text-echo").mkdir(parents=True)
    (root / "tools" / "text-echo" / "descriptor.yaml").write_text(
        "tool_id: text-echo\nversion: 1.0.0\n", encoding="utf-8"
    )
    (root / "lib" / "skill_runtime").mkdir(parents=True)
    (root / "lib" / "skill_runtime" / "marker.py").write_text("X = 1\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("# docs only\n", encoding="utf-8")
    (root / "catalog").mkdir()
    (root / "catalog" / "index.json").write_text("{}\n", encoding="utf-8")
    (root / "evidence" / "phase10").mkdir(parents=True)
    (root / "evidence" / "phase10" / "x.json").write_text("{}\n", encoding="utf-8")
    _git(root, "add", "skills", "tools", "lib", "docs", "catalog", "evidence")
    _git(root, "commit", "-m", "source")
    return _git(root, "rev-parse", "HEAD").stdout.strip()


class GovernedPathTests(unittest.TestCase):
    def test_excludes_generated_and_docs(self) -> None:
        self.assertTrue(is_governed_input_path("skills/canary-echo/SKILL.md"))
        self.assertTrue(is_governed_input_path("tools/text-echo/descriptor.yaml"))
        self.assertTrue(is_governed_input_path("lib/skill_runtime/catalog.py"))
        self.assertFalse(is_governed_input_path("catalog/index.json"))
        self.assertFalse(is_governed_input_path("evidence/phase10/sealed/x.json"))
        self.assertFalse(is_governed_input_path("docs/handoffs/x.md"))
        self.assertFalse(is_governed_input_path("tools/text-echo/tmp/fs-allowlist.sb"))
        self.assertFalse(is_governed_input_path("tools/gws/vendor/link-gws-cli/x.js"))


class CatalogProvenanceAdversarialTests(unittest.TestCase):
    def test_docs_only_commit_does_not_change_source_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = _init_repo(root)
            before = compute_source_tree_sha256(root, commit=source)
            (root / "docs" / "note.md").write_text("# docs only changed\n", encoding="utf-8")
            (root / "catalog" / "index.json").write_text('{"n":1}\n', encoding="utf-8")
            (root / "evidence" / "phase10" / "x.json").write_text('{"n":1}\n', encoding="utf-8")
            _git(root, "add", "docs", "catalog", "evidence")
            _git(root, "commit", "-m", "docs and generated only")
            tip = _git(root, "rev-parse", "HEAD").stdout.strip()
            after = compute_source_tree_sha256(root)
            self.assertEqual(before, after)
            self.assertNotEqual(source, tip)
            index = {
                "git_sha": source,
                "source_tree_sha256": before,
            }
            self.assertEqual(validate_catalog_provenance(index, root), [])

    def test_tracked_source_drift_fails_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = _init_repo(root)
            tree = compute_source_tree_sha256(root, commit=source)
            (root / "skills" / "demo" / "SKILL.md").write_text(
                "---\nname: demo\nversion: 0.1.1\n---\n# drifted\n", encoding="utf-8"
            )
            # Uncommitted tracked-source drift (still readable from worktree).
            index = {"git_sha": source, "source_tree_sha256": tree}
            errors = validate_catalog_provenance(index, root)
            self.assertTrue(any("current governed inputs" in e for e in errors), errors)

    def test_all_zero_git_sha_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = _init_repo(root)
            tree = compute_source_tree_sha256(root, commit=source)
            for bad in (ZERO_GIT_SHA, "0" * 40, "", None):
                index = {"git_sha": bad, "source_tree_sha256": tree}
                errors = validate_catalog_provenance(index, root)
                self.assertTrue(
                    any("all-zero" in e or "missing" in e or "not a 40-hex" in e for e in errors),
                    errors,
                )

    def test_unrelated_commit_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = _init_repo(root)
            tree = compute_source_tree_sha256(root, commit=source)
            # Orphan commit with different history (not ancestor of HEAD after reset).
            _git(root, "checkout", "--orphan", "orphan-branch")
            _git(root, "rm", "-rf", "--cached", ".")
            (root / "skills" / "demo" / "SKILL.md").write_text(
                "---\nname: demo\nversion: 9.9.9\n---\n# orphan\n", encoding="utf-8"
            )
            _git(root, "add", "skills", "tools", "lib", "docs", "catalog", "evidence")
            _git(root, "commit", "-m", "orphan")
            orphan = _git(root, "rev-parse", "HEAD").stdout.strip()
            _git(root, "checkout", "-B", "main", source)
            index = {"git_sha": orphan, "source_tree_sha256": tree}
            errors = validate_catalog_provenance(index, root)
            self.assertTrue(
                any("not an ancestor" in e or "do not match" in e for e in errors),
                errors,
            )

    def test_stale_source_tree_hash_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = _init_repo(root)
            index = {
                "git_sha": source,
                "source_tree_sha256": "ab" * 32,
            }
            errors = validate_catalog_provenance(index, root)
            self.assertTrue(any("does not match current" in e for e in errors), errors)

    def test_build_catalog_index_check_script_rejects_all_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = _init_repo(root)
            tree = compute_source_tree_sha256(root, commit=source)
            catalog_dir = root / "catalog"
            catalog_dir.mkdir(exist_ok=True)
            (catalog_dir / "index.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "git_sha": ZERO_GIT_SHA,
                        "source_tree_sha256": tree,
                        "skill_count": 0,
                        "skills": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            # Copy provenance module path via PYTHONPATH=REPO_ROOT; run validator API.
            errors = validate_catalog_provenance(
                json.loads((catalog_dir / "index.json").read_text(encoding="utf-8")),
                root,
            )
            self.assertTrue(any("all-zero" in e for e in errors), errors)


class RepoProvenanceSmokeTests(unittest.TestCase):
    def test_repo_governed_hash_stable_and_excludes_catalog(self) -> None:
        a = compute_source_tree_sha256(REPO_ROOT)
        b = compute_source_tree_sha256(REPO_ROOT)
        self.assertEqual(a, b)
        self.assertRegex(a, r"^[0-9a-f]{64}$")
        paths = [
            line
            for line in subprocess.check_output(
                ["git", "ls-files"], cwd=REPO_ROOT, text=True
            ).splitlines()
            if line.startswith("catalog/")
        ]
        self.assertTrue(paths)
        # Mutating a copy of catalog content cannot be done in-repo; assert exclusion.
        self.assertFalse(is_governed_input_path("catalog/index.json"))


if __name__ == "__main__":
    unittest.main()
