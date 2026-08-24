"""Protocol-independent policy and exact-resource primitives for MCP v2.

The MCP adapter owns transport and JSON-RPC concerns.  This module owns the
small, deterministic pieces that must remain true regardless of transport:
resource bytes are immutable, their digests are reproducible, and the four
eligibility gates are never collapsed into one caller-controlled flag.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .release_v2 import ReleaseError, inventory_digest, sha256


def _values(value: Any) -> frozenset[str]:
    """Normalize a role/profile/capability field to a bounded string set."""
    if value is None:
        return frozenset()
    if isinstance(value, str):
        return frozenset({value} if value else ())
    if isinstance(value, Mapping):
        return frozenset(str(k) for k, v in value.items() if v and str(k))
    try:
        return frozenset(str(item) for item in value if item is not None and str(item))
    except TypeError:
        return frozenset({str(value)})


@dataclass(frozen=True)
class ExactResource:
    """Immutable bytes and metadata for one addressable release resource."""

    resource_id: str
    body: bytes
    resource_kind: str = "entrypoint"
    media_type: str = "text/markdown"
    disclosure_level: int = 3
    provenance: Mapping[str, Any] = field(default_factory=dict)
    licence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.resource_id or not isinstance(self.body, bytes):
            raise ReleaseError("invalid_resource")
        if not 0 <= self.disclosure_level <= 6:
            raise ReleaseError("invalid_disclosure_level")

    @property
    def content_digest(self) -> str:
        """Return the digest of the exact bytes, never a substitute payload."""
        return sha256(self.body)

    def descriptor(self, skill_id: str, version: str) -> dict[str, Any]:
        """Build the PKT-01 exact-resource descriptor shape."""
        return {
            "schema_version": "0.1",
            "resource_id": self.resource_id,
            "release_id": f"{skill_id}@{version}",
            "skill_id": skill_id,
            "skill_version": version,
            "resource_kind": self.resource_kind,
            "resource_uri": (
                f"skills://release/{skill_id}/{version}/resource/{self.resource_id}"
            ),
            "media_type": self.media_type,
            "byte_size": len(self.body),
            "content_digest": self.content_digest,
            "immutable": True,
            "disclosure_level": self.disclosure_level,
            "provenance": dict(self.provenance),
            "licence": dict(self.licence),
            "trust_boundary": "linkskills-resource",
        }


@dataclass(frozen=True)
class GovernedRelease:
    """An exact release plus the policy metadata needed for retrieval."""

    skill_id: str
    version: str
    resources: tuple[ExactResource, ...]
    family_id: str = ""
    subcategory_id: str = ""
    collection_id: str = ""
    lifecycle_state: str = "qualified"
    qualification: str = "qualified"
    platform_technical_eligibility: bool = True
    skills_release_selectability: bool = True
    consumer_profile_activation: bool = True
    consumer_tool_authority: bool = True
    roles: frozenset[str] = frozenset()
    task_classes: frozenset[str] = frozenset()
    runtime_profiles: frozenset[str] = frozenset()
    required_capabilities: frozenset[str] = frozenset()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    applicability: Mapping[str, Any] = field(default_factory=dict)

    @property
    def release_id(self) -> str:
        """Return the immutable ``skill_id@version`` identity."""
        return f"{self.skill_id}@{self.version}"

    def resource(self, resource_id: str) -> ExactResource | None:
        """Find one exact resource without falling back to another release."""
        return next((item for item in self.resources if item.resource_id == resource_id), None)

    def verify_inventory(self) -> str:
        """Verify deterministic resource inventory and reject duplicate IDs."""
        files: dict[str, bytes] = {}
        for resource in self.resources:
            if resource.resource_id in files:
                raise ReleaseError("resource_id_collision")
            files[resource.resource_id] = resource.body
        return inventory_digest(files)


def gate_denials(
    release: GovernedRelease,
    *,
    roles: Any = None,
    task_class: Any = None,
    runtime_profile: Any = None,
    capabilities: Any = None,
    activated_release_ids: Any = None,
) -> tuple[str, ...]:
    """Return every failed independent gate, in stable order."""
    denials: list[str] = []
    if not release.platform_technical_eligibility:
        denials.append("platform_technical_eligibility")
    if not release.skills_release_selectability:
        denials.append("skills_release_selectability")
    if release.lifecycle_state not in {"qualified", "usable", "published"}:
        denials.append("release_not_selectable")
    if release.qualification not in {"qualified", "usable"}:
        denials.append("release_not_qualified")
    if not release.consumer_profile_activation:
        denials.append("consumer_profile_activation")
    if not release.consumer_tool_authority:
        denials.append("consumer_tool_authority")

    supplied_roles = _values(roles)
    if release.roles and not release.roles.intersection(supplied_roles):
        denials.append("role_not_authorized")
    supplied_tasks = _values(task_class)
    if release.task_classes and not release.task_classes.intersection(supplied_tasks):
        denials.append("task_not_authorized")
    supplied_profiles = _values(runtime_profile)
    if release.runtime_profiles and not release.runtime_profiles.intersection(supplied_profiles):
        denials.append("profile_not_compatible")
    supplied_capabilities = _values(capabilities)
    if release.required_capabilities and not release.required_capabilities.issubset(
        supplied_capabilities
    ):
        denials.append("capability_not_authorized")
    activated = _values(activated_release_ids)
    if activated and "*" not in activated and release.release_id not in activated:
        denials.append("profile_not_activated")
    return tuple(denials)


__all__ = ["ExactResource", "GovernedRelease", "gate_denials"]
