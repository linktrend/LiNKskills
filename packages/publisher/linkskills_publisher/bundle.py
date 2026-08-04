"""Build deterministic hashed Skill Pack bundles from a skill directory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from linkskills_core.hashing import (
    build_skill_bundle_manifest,
    content_hash_for_directory,
)


def content_hash_for_files(skill_dir: Path, files: list[Path] | None = None) -> tuple[str, list[dict[str, Any]]]:
    """Hash file contents in sorted relative-path order.

    Returns (content_hash, entry_hashes) where content_hash is ``sha256:<hex>``
    over the canonical manifest lines ``<relpath>\\0<file_sha256>\\n``.
    """
    return content_hash_for_directory(skill_dir, files=files)


def build_skill_bundle(skill_dir: str | Path) -> dict[str, Any]:
    """Build a deterministic Skill Pack bundle manifest from a skill directory."""
    return build_skill_bundle_manifest(skill_dir)
