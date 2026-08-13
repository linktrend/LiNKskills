"""Deterministic, provider-only immutable Skill Pack release primitives."""
from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Mapping


class ReleaseError(ValueError):
    """Typed fail-closed release verification error."""


def canonical_bytes(value: object) -> bytes:
    """Encode structured contract data deterministically."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256(value: object) -> str:
    """Return a canonical SHA-256 identifier; bytes are hashed as bytes."""
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def safe_relative_path(path: str) -> None:
    """Reject paths that cannot be safely materialized below the package root."""
    parsed = PurePosixPath(path)
    if not isinstance(path, str) or not path or parsed.is_absolute() or ".." in parsed.parts or "\\" in path or "//" in path:
        raise ReleaseError("unsafe_path")


def inventory_digest(files: Mapping[str, bytes]) -> str:
    """Hash a closed, deterministic inventory without following paths or executing files."""
    inventory: list[dict[str, str]] = []
    seen: set[str] = set()
    for path, body in sorted(files.items()):
        safe_relative_path(path)
        normalized = unicodedata.normalize("NFC", path).casefold()
        if normalized in seen:
            raise ReleaseError("inventory_path_collision")
        seen.add(normalized)
        if not isinstance(body, bytes):
            raise ReleaseError("invalid_file_body")
        inventory.append({"path": path, "digest": sha256(body), "size": len(body)})
    return sha256(inventory)


def assert_dependency_closure(release_id: str, dependencies: Mapping[str, tuple[str, ...]]) -> None:
    """Require an immutable, acyclic release dependency lock."""
    visiting: set[str] = set(); visited: set[str] = set()
    def visit(node: str) -> None:
        if node in visiting: raise ReleaseError("dependency_cycle")
        if node in visited: return
        if node not in dependencies: raise ReleaseError("dependency_missing")
        visiting.add(node)
        for child in dependencies[node]: visit(child)
        visiting.remove(node); visited.add(node)
    visit(release_id)


@dataclass(frozen=True)
class ReleaseManifest:
    """A complete exact-release record; content never changes after publication."""
    skill_id: str
    version: str
    files_digest: str
    package_digest: str
    lifecycle: str = "published"
    qualification: str = "qualified"
    contract_version: str = "skills-release/0.2"
    qualification_profile: str = "default"
    qualification_evidence_ref: str = ""
    provenance: Mapping[str, str] = field(default_factory=dict)
    source_ref: str = ""
    license_ref: str = ""
    dependency_lock: tuple[str, ...] = ()
    applicability: Mapping[str, Any] = field(default_factory=dict)
    published_at: str = ""
    max_package_bytes: int = 10_000_000

    @property
    def release_id(self) -> str:
        return f"{self.skill_id}@{self.version}"

    def canonical_claims(self) -> dict[str, Any]:
        """Return the immutable claims covered by a publisher attestation."""
        return {"release_id": self.release_id, "skill_id": self.skill_id, "version": self.version,
                "files_digest": self.files_digest, "package_digest": self.package_digest,
                "qualification_profile": self.qualification_profile, "published_at": self.published_at,
                "contract_version": self.contract_version}

    def verify(self, files: Mapping[str, bytes], *, availability: str = "available", dependencies: Mapping[str, tuple[str, ...]] | None = None) -> str:
        """Verify exactly the pinned bytes; never select a substitute release."""
        if availability in {"revoked", "quarantined", "withdrawn", "offline", "disabled", "stale", "incompatible"}:
            raise ReleaseError(availability)
        if self.lifecycle not in {"published", "deprecated"}: raise ReleaseError("not_published")
        if self.qualification != "qualified": raise ReleaseError("not_qualified")
        if inventory_digest(files) != self.files_digest: raise ReleaseError("integrity_mismatch")
        if sum(len(body) for body in files.values()) > self.max_package_bytes: raise ReleaseError("package_too_large")
        expected = sha256({"release_id": self.release_id, "files_digest": self.files_digest,
                           "contract_version": self.contract_version})
        if expected != self.package_digest: raise ReleaseError("package_mismatch")
        if dependencies is not None: assert_dependency_closure(self.release_id, dependencies)
        return "deprecated_warning" if self.lifecycle == "deprecated" else "verified"
