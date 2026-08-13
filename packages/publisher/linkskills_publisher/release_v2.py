"""In-memory publisher registry; consumers select, this module never executes."""
from __future__ import annotations
from dataclasses import dataclass
from linkskills_core.release_v2 import ReleaseError, ReleaseManifest, inventory_digest, sha256

@dataclass(frozen=True)
class PublisherAttestation:
    algorithm: str; key_id: str; organization: str; audience: str; capability: str; state: str = "active"
    def verify_metadata(self, *, organization: str, audience: str, capability: str) -> None:
        if self.algorithm != "ES256": raise ReleaseError("attestation_algorithm")
        if self.state != "active": raise ReleaseError("attestation_key_revoked")
        if (self.organization, self.audience, self.capability) != (organization, audience, capability): raise ReleaseError("attestation_trust_mismatch")

class ReleaseRegistry:
    def __init__(self) -> None: self._releases = {}; self._current = {}
    def publish(self, skill_id: str, version: str, files: dict[str, bytes]) -> ReleaseManifest:
        fd = inventory_digest(files); manifest = ReleaseManifest(skill_id, version, fd, sha256({"release_id": f"{skill_id}@{version}", "files_digest": fd}))
        if manifest.release_id in self._releases: raise ReleaseError("immutable_release_exists")
        self._releases[manifest.release_id] = (manifest, dict(files)); return manifest
    def exact(self, skill_id: str, version: str) -> ReleaseManifest:
        try: return self._releases[f"{skill_id}@{version}"][0]
        except KeyError as exc: raise ReleaseError("release_not_found") from exc
    def set_current(self, skill_id: str, version: str, expected: str | None) -> None:
        if self._current.get(skill_id) != expected: raise ReleaseError("current_pointer_conflict")
        self.exact(skill_id, version); self._current[skill_id] = version
    def verify(self, skill_id: str, version: str, files: dict[str, bytes], *, availability: str = "available") -> str:
        return self.exact(skill_id, version).verify(files, availability=availability)
