"""In-memory immutable publisher registry; this module never executes a Skill Pack."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from linkskills_core.release_v2 import ReleaseError, ReleaseManifest, canonical_bytes, inventory_digest, sha256


@dataclass(frozen=True)
class PublisherAttestation:
    """Detached ES256 claim envelope verified through an injected trusted key resolver."""
    algorithm: str; key_id: str; organization: str; audience: str; capability: str
    state: str = "active"; signature: bytes = b""

    def verify_metadata(self, *, organization: str, audience: str, capability: str) -> None:
        if self.algorithm != "ES256": raise ReleaseError("attestation_algorithm")
        if self.state != "active": raise ReleaseError("attestation_key_revoked")
        if not self.key_id: raise ReleaseError("attestation_key_unknown")
        if (self.organization, self.audience, self.capability) != (organization, audience, capability):
            raise ReleaseError("attestation_trust_mismatch")

    def verify(self, manifest: ReleaseManifest, *, verifier: Callable[[str, bytes, bytes], bool], organization: str, audience: str, capability: str) -> None:
        self.verify_metadata(organization=organization, audience=audience, capability=capability)
        if not self.signature or not verifier(self.key_id, canonical_bytes(manifest.canonical_claims()), self.signature):
            raise ReleaseError("attestation_signature_invalid")


class ReleaseRegistry:
    """Maintains immutable releases and auditable atomic current pointers."""
    def __init__(self) -> None:
        self._releases: dict[str, tuple[ReleaseManifest, dict[str, bytes]]] = {}
        self._current: dict[str, str] = {}; self._pointer_history: list[tuple[str, str | None, str]] = []

    def publish(self, skill_id: str, version: str, files: dict[str, bytes], **metadata: Any) -> ReleaseManifest:
        fd = inventory_digest(files)
        contract_version = str(metadata.get("contract_version", "skills-release/0.2"))
        manifest = ReleaseManifest(skill_id, version, fd, sha256({"release_id": f"{skill_id}@{version}", "files_digest": fd, "contract_version": contract_version}), **metadata)
        if manifest.release_id in self._releases: raise ReleaseError("immutable_release_exists")
        self._releases[manifest.release_id] = (manifest, dict(files)); return manifest

    def exact(self, skill_id: str, version: str) -> ReleaseManifest:
        try: return self._releases[f"{skill_id}@{version}"][0]
        except KeyError as exc: raise ReleaseError("release_not_found") from exc

    def set_current(self, skill_id: str, version: str, expected: str | None) -> None:
        if self._current.get(skill_id) != expected: raise ReleaseError("current_pointer_conflict")
        self.exact(skill_id, version); self._current[skill_id] = version; self._pointer_history.append((skill_id, expected, version))

    def verify(self, skill_id: str, version: str, files: dict[str, bytes], *, availability: str = "available") -> str:
        return self.exact(skill_id, version).verify(files, availability=availability)
