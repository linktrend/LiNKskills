"""Pure immutable release primitives for the provider-only v2 surface."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Mapping


class ReleaseError(ValueError):
    """Typed fail-closed release error."""


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha256(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def safe_relative_path(path: str) -> None:
    parsed = PurePosixPath(path)
    if not path or parsed.is_absolute() or ".." in parsed.parts or "\\" in path:
        raise ReleaseError("unsafe_path")


def inventory_digest(files: Mapping[str, bytes]) -> str:
    inventory: list[dict[str, str]] = []
    for path, body in sorted(files.items()):
        safe_relative_path(path)
        inventory.append({"path": path, "digest": "sha256:" + hashlib.sha256(body).hexdigest()})
    return sha256(inventory)


def assert_dependency_closure(release_id: str, dependencies: Mapping[str, tuple[str, ...]]) -> None:
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
    skill_id: str
    version: str
    files_digest: str
    package_digest: str
    lifecycle: str = "published"
    qualification: str = "qualified"

    @property
    def release_id(self) -> str:
        return f"{self.skill_id}@{self.version}"

    def verify(self, files: Mapping[str, bytes], *, availability: str = "available") -> str:
        if availability in {"revoked", "quarantined", "withdrawn", "offline", "disabled"}: raise ReleaseError(availability)
        if self.lifecycle not in {"published", "deprecated"}: raise ReleaseError("not_published")
        if self.qualification != "qualified": raise ReleaseError("not_qualified")
        if inventory_digest(files) != self.files_digest: raise ReleaseError("integrity_mismatch")
        if sha256({"release_id": self.release_id, "files_digest": self.files_digest}) != self.package_digest: raise ReleaseError("package_mismatch")
        return "deprecated_warning" if self.lifecycle == "deprecated" else "verified"
