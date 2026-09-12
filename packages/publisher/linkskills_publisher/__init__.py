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
from .initial_set import (
    ALLOWLIST_RELEASE_IDS,
    INITIAL_ALLOWLIST,
    InitialReleaseSpec,
    ORDINARY_SELECTABLE_COUNT,
    PublicationError,
    SourceOnlyInitialPublisher,
    catalog_skill_count,
    publish_exact_initial_releases,
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
    "ALLOWLIST_RELEASE_IDS",
    "INITIAL_ALLOWLIST",
    "InitialReleaseSpec",
    "ORDINARY_SELECTABLE_COUNT",
    "PublicationError",
    "SourceOnlyInitialPublisher",
    "catalog_skill_count",
    "publish_exact_initial_releases",
]

__version__ = "0.1.0"
