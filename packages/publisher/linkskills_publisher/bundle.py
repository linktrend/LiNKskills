"""Build deterministic hashed Skill Pack bundles from a skill directory."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_skill_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        # Skip editor/OS noise; keep skill content deterministic.
        if path.name in {".DS_Store", "Thumbs.db"}:
            continue
        if path.name.startswith("."):
            continue
        files.append(path)
    return files


def content_hash_for_files(skill_dir: Path, files: list[Path] | None = None) -> tuple[str, list[dict[str, Any]]]:
    """Hash file contents in sorted relative-path order.

    Returns (content_hash, entry_hashes) where content_hash is ``sha256:<hex>``
    over the canonical manifest lines ``<relpath>\\0<file_sha256>\\n``.
    """
    root = skill_dir.resolve()
    entries = files if files is not None else _iter_skill_files(root)
    entry_hashes: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    for path in sorted(entries, key=lambda p: p.resolve().relative_to(root).as_posix()):
        rel = path.resolve().relative_to(root).as_posix()
        file_hash = _sha256_file(path)
        size = path.stat().st_size
        entry_hashes.append({"path": rel, "sha256": file_hash, "size": size})
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}", entry_hashes


def _parse_simple_frontmatter(text: str) -> dict[str, Any]:
    """Minimal YAML-ish frontmatter parser for name/version without requiring PyYAML."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    meta: dict[str, Any] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in {"name", "version", "description", "format_profile"}:
            meta[key] = value
    return meta


def _discover_fragments(skill_dir: Path, entry_hashes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fragments: list[dict[str, Any]] = []
    by_path = {e["path"]: e["sha256"] for e in entry_hashes}
    if "SKILL.md" in by_path:
        fragments.append(
            {
                "fragment_id": "skill-md",
                "disclosure_level": 2,
                "path": "SKILL.md",
                "content_hash": f"sha256:{by_path['SKILL.md']}",
            }
        )
    for path in sorted(by_path):
        if path.startswith("references/") and path.endswith((".md", ".yaml", ".yml", ".json")):
            level = 5 if "example" in path or "schema" in path else 3
            if path.endswith("eval-suite.yaml") or path.endswith("eval-suite.yml"):
                continue
            fragments.append(
                {
                    "fragment_id": path.replace("/", "__"),
                    "disclosure_level": level,
                    "path": path,
                    "content_hash": f"sha256:{by_path[path]}",
                }
            )
    return fragments


def _eval_suite_hash(skill_dir: Path) -> str | None:
    for candidate in (
        skill_dir / "references" / "eval-suite.yaml",
        skill_dir / "references" / "eval-suite.yml",
    ):
        if candidate.is_file():
            return f"sha256:{_sha256_file(candidate)}"
    return None


def build_skill_bundle(skill_dir: str | Path) -> dict[str, Any]:
    """Build a deterministic Skill Pack bundle manifest from a skill directory."""
    root = Path(skill_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"skill directory not found: {root}")

    skill_md = root / "SKILL.md"
    meta: dict[str, Any] = {}
    if skill_md.is_file():
        meta = _parse_simple_frontmatter(skill_md.read_text(encoding="utf-8"))

    skill_id = str(meta.get("name") or root.name)
    version = str(meta.get("version") or "0.0.0")

    content_hash, entry_hashes = content_hash_for_files(root)
    fragments = _discover_fragments(root, entry_hashes)
    eval_hash = _eval_suite_hash(root)

    manifest: dict[str, Any] = {
        "schema_version": "0.1",
        "skill_id": skill_id,
        "version": version,
        "content_hash": content_hash,
        "fragments": fragments,
        "eval_suite_hash": eval_hash,
        "file_count": len(entry_hashes),
        "entry_hashes": entry_hashes,
    }
    # Include a stable JSON fingerprint of the manifest identity fields.
    identity = {
        "skill_id": skill_id,
        "version": version,
        "content_hash": content_hash,
        "eval_suite_hash": eval_hash,
        "fragments": [{"path": f["path"], "content_hash": f["content_hash"]} for f in fragments],
    }
    identity_bytes = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest["bundle_hash"] = f"sha256:{_sha256_bytes(identity_bytes)}"
    return manifest
