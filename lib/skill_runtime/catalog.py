"""Filesystem catalog index for consumer Programs.

``catalog/index.json`` is the lightweight discovery surface. Certification state
from ``lskills.catalog`` is optional overlay data — when unavailable, entries
default to ``draft`` (filesystem presence alone does not mean ``usable``).
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass(frozen=True)
class CatalogEntry:
    """One skill version discoverable by consumers."""

    skill_id: str
    version: str
    path: str
    description: str
    format_profile: str
    eval_suite_ref: str
    certification_state: str
    min_reasoning_tier: Optional[str] = None
    usage_trigger: Optional[str] = None
    release_hash: Optional[str] = None
    profile_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        # Omit null optional hashes so draft rows stay compact.
        if not payload.get("release_hash"):
            payload.pop("release_hash", None)
        if not payload.get("profile_hash"):
            payload.pop("profile_hash", None)
        return payload


def _parse_frontmatter_scalar_block(text: str) -> Dict[str, str]:
    """Extract flat string keys from SKILL.md YAML frontmatter without full YAML."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    block = match.group(1)
    result: Dict[str, str] = {}
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        # Skip nested indented keys (engine., tooling., etc.)
        if raw.startswith(" ") or raw.startswith("\t"):
            key = line.split(":", 1)[0].strip()
            if key in {"min_reasoning_tier"}:
                value = line.split(":", 1)[1].strip().strip("\"'")
                result[key] = value
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key in {
            "name",
            "description",
            "version",
            "usage_trigger",
            "format_profile",
        }:
            result[key] = value
    return result


def discover_skill_dirs(repo_root: Path) -> List[Path]:
    skills_root = repo_root / "skills"
    if not skills_root.is_dir():
        return []
    return sorted(
        path.parent.resolve()
        for path in skills_root.glob("*/SKILL.md")
        if path.is_file()
    )


def build_catalog_entries(
    repo_root: Path,
    *,
    certification_overlay: Optional[Dict[str, str]] = None,
    hash_overlay: Optional[Dict[str, Dict[str, str]]] = None,
) -> List[CatalogEntry]:
    """Build catalog entries from on-disk skills.

    ``certification_overlay`` maps ``skill_id`` → ``certification_state`` from
    the classification ledger (or ``lskills.catalog`` when a live DB is
    available). Missing keys stay ``draft``.

    ``hash_overlay`` optionally maps ``skill_id`` → ``{release_hash, profile_hash}``
    from sealed certification evidence.
    """
    overlay = certification_overlay or {}
    hashes = hash_overlay or {}
    entries: List[CatalogEntry] = []
    for skill_dir in discover_skill_dirs(repo_root):
        skill_md = skill_dir / "SKILL.md"
        meta = _parse_frontmatter_scalar_block(skill_md.read_text(encoding="utf-8"))
        skill_id = skill_dir.name
        version = meta.get("version", "0.0.0")
        eval_suite_ref = f"skills/{skill_id}/references/eval-suite.yaml"
        hash_meta = hashes.get(skill_id) or {}
        entries.append(
            CatalogEntry(
                skill_id=skill_id,
                version=version,
                path=f"skills/{skill_id}",
                description=meta.get("description", ""),
                format_profile=meta.get("format_profile", "heavy"),
                eval_suite_ref=eval_suite_ref,
                certification_state=overlay.get(skill_id, "draft"),
                min_reasoning_tier=meta.get("min_reasoning_tier"),
                usage_trigger=meta.get("usage_trigger"),
                release_hash=hash_meta.get("release_hash") or hash_meta.get("skill_release_hash"),
                profile_hash=hash_meta.get("profile_hash"),
            )
        )
    return entries


def build_catalog_index(
    repo_root: Path,
    *,
    certification_overlay: Optional[Dict[str, str]] = None,
    hash_overlay: Optional[Dict[str, Dict[str, str]]] = None,
    git_sha: Optional[str] = None,
) -> Dict[str, Any]:
    entries = build_catalog_entries(
        repo_root,
        certification_overlay=certification_overlay,
        hash_overlay=hash_overlay,
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root_marker": "LiNKskills",
        "git_sha": git_sha,
        "skill_count": len(entries),
        "skills": [entry.to_dict() for entry in entries],
    }


def write_catalog_index(repo_root: Path, index: Dict[str, Any]) -> Path:
    out_dir = repo_root / "catalog"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.json"
    out_path.write_text(
        json.dumps(index, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return out_path


def load_catalog_index(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / "catalog" / "index.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {path}; run scripts/build-catalog-index.py first"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def list_skills(
    index: Dict[str, Any],
    *,
    usable_only: bool = False,
    include_states: Optional[Iterable[str]] = None,
) -> List[CatalogEntry]:
    allowed = set(include_states) if include_states is not None else None
    if usable_only:
        allowed = {"usable"}
    results: List[CatalogEntry] = []
    for raw in index.get("skills", []):
        state = raw.get("certification_state", "draft")
        if allowed is not None and state not in allowed:
            continue
        results.append(
            CatalogEntry(
                skill_id=raw["skill_id"],
                version=raw["version"],
                path=raw["path"],
                description=raw.get("description", ""),
                format_profile=raw.get("format_profile", "heavy"),
                eval_suite_ref=raw["eval_suite_ref"],
                certification_state=state,
                min_reasoning_tier=raw.get("min_reasoning_tier"),
                usage_trigger=raw.get("usage_trigger"),
                release_hash=raw.get("release_hash") or raw.get("skill_release_hash"),
                profile_hash=raw.get("profile_hash"),
            )
        )
    return results
