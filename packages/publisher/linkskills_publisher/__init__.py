"""LiNKskills publisher: deterministic Skill Pack bundles and frontmatter helpers."""

from .bundle import build_skill_bundle, content_hash_for_files
from .migrate_frontmatter import migrate_legacy_frontmatter, migrate_dependencies
from .registry import PublisherRegistry, PublishedRelease

try:
    from .postgres_registry import PostgresPublisherRegistry, open_publisher_registry
except ImportError:  # pragma: no cover — optional psycopg
    PostgresPublisherRegistry = None  # type: ignore[misc, assignment]
    open_publisher_registry = None  # type: ignore[misc, assignment]

__all__ = [
    "PublishedRelease",
    "PublisherRegistry",
    "PostgresPublisherRegistry",
    "build_skill_bundle",
    "content_hash_for_files",
    "migrate_legacy_frontmatter",
    "migrate_dependencies",
    "open_publisher_registry",
]

__version__ = "0.1.0"
