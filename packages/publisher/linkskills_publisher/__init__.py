"""LiNKskills publisher: deterministic Skill Pack bundles and frontmatter helpers."""

from .bundle import build_skill_bundle, content_hash_for_files
from .migrate_frontmatter import migrate_legacy_frontmatter, migrate_dependencies

__all__ = [
    "build_skill_bundle",
    "content_hash_for_files",
    "migrate_legacy_frontmatter",
    "migrate_dependencies",
]

__version__ = "0.1.0"
