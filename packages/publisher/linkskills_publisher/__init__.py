"""LiNKskills publisher: deterministic Skill Pack bundles and frontmatter helpers."""

from .bundle import build_skill_bundle, content_hash_for_files
from .migrate_frontmatter import migrate_legacy_frontmatter, migrate_dependencies
from .postgres_registry import PostgresPublisherRegistry, open_publisher_registry
from .registry import PublisherRegistry, PublishedRelease
from .external_lifecycle import (
    AdaptedRelease,
    CollectionManifest,
    ExternalCollectionLifecycle,
    FileProvenance,
    LifecycleError,
    ReviewOutcome,
    UpdateCandidate,
    VendorRelease,
)

__all__ = [
    "PublishedRelease",
    "PublisherRegistry",
    "PostgresPublisherRegistry",
    "build_skill_bundle",
    "content_hash_for_files",
    "migrate_legacy_frontmatter",
    "migrate_dependencies",
    "open_publisher_registry",
    "AdaptedRelease",
    "CollectionManifest",
    "ExternalCollectionLifecycle",
    "FileProvenance",
    "LifecycleError",
    "ReviewOutcome",
    "UpdateCandidate",
    "VendorRelease",
]

__version__ = "0.1.0"
