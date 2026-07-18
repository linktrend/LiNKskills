"""Resolve and load skill progressive-disclosure bundles from a LiNKskills checkout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .catalog import CatalogEntry, load_catalog_index, list_skills


@dataclass(frozen=True)
class SkillBundle:
    """Resolved on-disk skill package for a consumer agent."""

    skill_id: str
    version: str
    root: Path
    skill_md: Path
    eval_suite: Path
    certification_state: str
    format_profile: str
    disclosure_paths: Dict[str, Path]


def resolve_repo_root(explicit: Optional[Path] = None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    # lib/skill_runtime/loader.py → repo root is parents[2]
    return Path(__file__).resolve().parents[2]


def resolve_skill_path(skill_id: str, repo_root: Optional[Path] = None) -> Path:
    root = resolve_repo_root(repo_root)
    path = root / "skills" / skill_id
    if not (path / "SKILL.md").is_file():
        raise FileNotFoundError(f"Skill '{skill_id}' not found under {root / 'skills'}")
    return path


def _entry_for(skill_id: str, repo_root: Path) -> Optional[CatalogEntry]:
    index_path = repo_root / "catalog" / "index.json"
    if not index_path.is_file():
        return None
    index = load_catalog_index(repo_root)
    for entry in list_skills(index):
        if entry.skill_id == skill_id:
            return entry
    return None


def load_skill(
    skill_id: str,
    *,
    repo_root: Optional[Path] = None,
    require_usable: bool = False,
) -> SkillBundle:
    """Load a skill bundle.

    When ``require_usable`` is True, the catalog index must list the skill as
    ``usable``. Until the Librarian certifies skills, leave this False and treat
    filesystem presence as the operational source for agent instruction loading.
    """
    root = resolve_repo_root(repo_root)
    skill_dir = resolve_skill_path(skill_id, root)
    entry = _entry_for(skill_id, root)
    certification_state = entry.certification_state if entry else "draft"
    version = entry.version if entry else "unknown"
    format_profile = entry.format_profile if entry else "heavy"

    if require_usable and certification_state != "usable":
        raise PermissionError(
            f"Skill '{skill_id}' certification_state is '{certification_state}', "
            "not 'usable'. Wait for Librarian certification or set require_usable=False."
        )

    skill_md = skill_dir / "SKILL.md"
    eval_suite = skill_dir / "references" / "eval-suite.yaml"
    if not eval_suite.is_file():
        raise FileNotFoundError(
            f"Skill '{skill_id}' is missing references/eval-suite.yaml"
        )

    disclosure: Dict[str, Path] = {"SKILL.md": skill_md}
    for rel in (
        "advanced",
        "examples",
        "references",
        "scripts",
    ):
        candidate = skill_dir / rel
        if candidate.exists():
            disclosure[rel] = candidate

    return SkillBundle(
        skill_id=skill_id,
        version=version,
        root=skill_dir,
        skill_md=skill_md,
        eval_suite=eval_suite,
        certification_state=certification_state,
        format_profile=format_profile,
        disclosure_paths=disclosure,
    )


def read_skill_md(skill_id: str, repo_root: Optional[Path] = None) -> str:
    bundle = load_skill(skill_id, repo_root=repo_root, require_usable=False)
    return bundle.skill_md.read_text(encoding="utf-8")


def list_loadable_skill_ids(
    repo_root: Optional[Path] = None,
    *,
    usable_only: bool = False,
) -> List[str]:
    root = resolve_repo_root(repo_root)
    index_path = root / "catalog" / "index.json"
    if index_path.is_file():
        return [e.skill_id for e in list_skills(load_catalog_index(root), usable_only=usable_only)]
    return [p.name for p in sorted((root / "skills").iterdir()) if (p / "SKILL.md").is_file()]
