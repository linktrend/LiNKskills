"""Source-only publication of the exact five initial qualified releases.

This module never mutates a live provider, spends, opens a PR, merges, deploys,
or writes consumer activation. It binds exact source/bundle/eval/tool/profile
digests, keeps the three eligibility gates independent, and treats ordinary
selectability as the explicit allowlist length rather than catalogue size.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from linkskills_core.hashing import build_skill_bundle_manifest
from linkskills_core.release_v2 import ReleaseError, inventory_digest, sha256

from .release_v2 import ReleaseRegistry

SCHEMA_VERSION = "0.1"
PUBLICATION_KIND = "ed-04-source-only-initial-publication"
INTENDED_CHANNEL = "internal"
ORDINARY_SELECTABLE_COUNT = 5
EVALUATED_BY = "linkskills-publisher-source-only"
LIVE_PROVIDER_MUTATION = False
CONSUMER_CONFIGURATION = False

QUARANTINED = "quarantined"
REVOKED = "revoked"
AVAILABLE = "available"


class PublicationError(ValueError):
    """Fail-closed source publication or selectability error."""


@dataclass(frozen=True)
class InitialReleaseSpec:
    """One frozen initial release/profile identity from the delivery lock."""

    skill_id: str
    version: str
    runtime_profile: str

    @property
    def release_id(self) -> str:
        """Return ``skill_id@version``."""
        return f"{self.skill_id}@{self.version}"

    @property
    def combination_id(self) -> str:
        """Return the ED-03 combination identity."""
        return f"{self.skill_id}@{self.version}/{self.runtime_profile}"


INITIAL_ALLOWLIST: tuple[InitialReleaseSpec, ...] = (
    InitialReleaseSpec("git-safeguard", "1.1.0", "cursor-macos"),
    InitialReleaseSpec("persistent-qa", "1.0.0", "cursor-macos"),
    InitialReleaseSpec("repository-manager", "1.0.0", "cursor-macos"),
    InitialReleaseSpec("skill-template", "1.2.0", "cursor-macos"),
    InitialReleaseSpec("tool-architect", "1.0.0", "cursor-macos"),
)

ALLOWLIST_RELEASE_IDS: frozenset[str] = frozenset(item.release_id for item in INITIAL_ALLOWLIST)


def _digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _opaque_ref(*parts: str) -> str:
    body = ":".join(parts)
    return f"opaque:{body}"


def _skill_dir(repo_root: Path, skill_id: str) -> Path:
    return repo_root / "skills" / skill_id


def collect_skill_files(skill_dir: Path) -> dict[str, bytes]:
    """Load governed skill files without following parent paths."""
    root = skill_dir.resolve()
    if not root.is_dir():
        raise PublicationError(f"skill_dir_missing:{root.as_posix()}")
    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        files[rel.as_posix()] = path.read_bytes()
    if not files:
        raise PublicationError(f"skill_dir_empty:{root.as_posix()}")
    return files


def _tool_digest(skill_dir: Path, pack: Mapping[str, Any]) -> str:
    deps = pack.get("dependencies") if isinstance(pack.get("dependencies"), Mapping) else {}
    tools = deps.get("packaged_tools") if isinstance(deps, Mapping) else []
    if not isinstance(tools, list) or not tools:
        return sha256({"packaged_tools": []})
    return sha256({"packaged_tools": tools})


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PublicationError(f"json_not_object:{path.as_posix()}")
    return data


def _gate(*, status: bool, evidence_ref: str) -> dict[str, Any]:
    return {
        "status": bool(status),
        "evidence_ref": evidence_ref,
        "evaluated_by": EVALUATED_BY,
    }


def allowlist_spec(skill_id: str, version: str) -> InitialReleaseSpec | None:
    """Return the allowlist row for an exact skill/version, if any."""
    wanted = f"{skill_id}@{version}"
    for item in INITIAL_ALLOWLIST:
        if item.release_id == wanted:
            return item
    return None


def matrix_row(
    matrix: Mapping[str, Any] | None,
    spec: InitialReleaseSpec,
) -> dict[str, Any] | None:
    """Find the ED-03 combination row without rewriting sibling state."""
    if not matrix:
        return None
    rows = matrix.get("combinations")
    if not isinstance(rows, list):
        return None
    wanted = spec.combination_id
    for row in rows:
        if isinstance(row, Mapping) and str(row.get("id") or "") == wanted:
            return dict(row)
    return None


def _lifecycle_for(spec: InitialReleaseSpec, matrix: Mapping[str, Any] | None) -> str:
    row = matrix_row(matrix, spec)
    if row is None:
        return "already_qualified"
    lifecycle = str(row.get("lifecycle") or "").strip()
    return lifecycle or "already_qualified"


@dataclass
class SourceOnlyInitialPublisher:
    """In-memory publisher for the frozen initial set. No live store I/O."""

    live_provider_mutation: bool = field(default=LIVE_PROVIDER_MUTATION, init=False)
    consumer_configuration: bool = field(default=CONSUMER_CONFIGURATION, init=False)

    def __post_init__(self) -> None:
        self._registry = ReleaseRegistry()
        self._records: dict[str, dict[str, Any]] = {}
        self._files: dict[str, dict[str, bytes]] = {}
        self._pointers: dict[str, str] = {}
        self._pointer_history: list[tuple[str, str | None, str]] = []
        self._availability: dict[str, str] = {}
        self._matrix: dict[str, Any] | None = None

    def publish_initial_set(
        self,
        repo_root: str | Path,
        *,
        qualification_matrix: Mapping[str, Any] | None = None,
        catalog_skill_count: int | None = None,
    ) -> dict[str, Any]:
        """Publish exactly the allowlisted initial releases from source trees."""
        root = Path(repo_root).resolve()
        if qualification_matrix is not None:
            self._matrix = dict(qualification_matrix)
            if self._matrix.get("complete") is False:
                raise PublicationError("qualification_matrix_incomplete")
        published: list[dict[str, Any]] = []
        for spec in INITIAL_ALLOWLIST:
            published.append(self._publish_spec(root, spec))
        if len(published) != ORDINARY_SELECTABLE_COUNT:
            raise PublicationError("initial_publication_count_invalid")
        selectable = self.selectable_releases()
        if len(selectable) != ORDINARY_SELECTABLE_COUNT:
            raise PublicationError("ordinary_selectable_count_invalid")
        if catalog_skill_count is not None and len(selectable) == catalog_skill_count:
            raise PublicationError("selectable_count_must_not_equal_catalog_count")
        return self.receipt(catalog_skill_count=catalog_skill_count)

    def _publish_spec(self, root: Path, spec: InitialReleaseSpec) -> dict[str, Any]:
        lifecycle = _lifecycle_for(spec, self._matrix)
        if lifecycle == QUARANTINED:
            raise PublicationError(f"quarantined:{spec.combination_id}")
        skill_dir = _skill_dir(root, spec.skill_id)
        files = collect_skill_files(skill_dir)
        bundle = build_skill_bundle_manifest(skill_dir)
        if str(bundle["skill_id"]) != spec.skill_id:
            raise PublicationError(f"skill_id_mismatch:{bundle['skill_id']}")
        if str(bundle["version"]) != spec.version:
            raise PublicationError(f"version_mismatch:{bundle['version']}")
        pack = _load_json_object(skill_dir / "references" / "skill-pack.json")
        profile_path = skill_dir / "references" / "execution-profile.json"
        profile_raw = profile_path.read_bytes() if profile_path.is_file() else b"{}"
        eval_digest = str(bundle.get("eval_suite_hash") or sha256(b""))
        tool_digest = _tool_digest(skill_dir, pack)
        profile_digest = _digest_bytes(profile_raw)
        source_digest = str(bundle["content_hash"])
        bundle_digest = str(bundle["bundle_hash"])
        files_digest = inventory_digest(files)
        if spec.release_id in self._records:
            existing = self._records[spec.release_id]
            if existing["filesDigest"] != files_digest:
                raise PublicationError(f"immutable_release_conflict:{spec.release_id}")
            return existing
        manifest = self._registry.publish(
            spec.skill_id,
            spec.version,
            files,
            qualification_profile=spec.runtime_profile,
            qualification_evidence_ref=_opaque_ref("ed-03", spec.combination_id),
            source_ref=spec.combination_id,
        )
        if manifest.files_digest != files_digest:
            raise PublicationError("files_digest_mismatch")
        technical = _gate(
            status=True,
            evidence_ref=_opaque_ref("bundle", bundle_digest.removeprefix("sha256:")),
        )
        selectable = _gate(
            status=True,
            evidence_ref=_opaque_ref("allowlist", spec.release_id),
        )
        activation = _gate(
            status=False,
            evidence_ref=_opaque_ref("consumer-activation", "not-configured"),
        )
        record = {
            "skillId": spec.skill_id,
            "version": spec.version,
            "runtimeProfile": spec.runtime_profile,
            "releaseId": spec.release_id,
            "combinationId": spec.combination_id,
            "channel": INTENDED_CHANNEL,
            "availability": AVAILABLE,
            "qualificationLifecycle": lifecycle,
            "sourceDigest": source_digest,
            "bundleDigest": bundle_digest,
            "evalDigest": eval_digest,
            "toolDigest": tool_digest,
            "profileDigest": profile_digest,
            "filesDigest": files_digest,
            "packageDigest": manifest.package_digest,
            "platformTechnicalEligibility": technical,
            "skillsReleaseSelectability": selectable,
            "consumerProfileActivation": activation,
            "liveProviderMutation": False,
            "consumerConfiguration": False,
        }
        self._records[spec.release_id] = record
        self._files[spec.release_id] = files
        self._availability[spec.release_id] = AVAILABLE
        previous = self._pointers.get(spec.skill_id)
        self._registry.set_current(spec.skill_id, spec.version, previous)
        self._pointers[spec.skill_id] = spec.version
        self._pointer_history.append((spec.skill_id, previous, spec.version))
        return record

    def retrieve_exact(
        self,
        skill_id: str,
        version: str,
        *,
        digest: str | None = None,
    ) -> dict[str, Any]:
        """Return one published release by exact version and optional digest."""
        release_id = f"{skill_id}@{version}"
        record = self._records.get(release_id)
        if record is None:
            raise PublicationError("release_not_found")
        availability = self._availability.get(release_id, AVAILABLE)
        if availability in {REVOKED, QUARANTINED}:
            raise PublicationError(availability)
        files = self._files[release_id]
        try:
            self._registry.verify(skill_id, version, files, availability=availability)
        except ReleaseError as exc:
            raise PublicationError(str(exc)) from exc
        if digest:
            allowed = {
                record["filesDigest"],
                record["bundleDigest"],
                record["packageDigest"],
                record["sourceDigest"],
            }
            if digest not in allowed:
                raise PublicationError("digest_mismatch")
        return dict(record)

    def evaluate_request(
        self,
        *,
        skill_id: str,
        version: str,
        runtime_profile: str,
        digest: str | None = None,
    ) -> dict[str, Any]:
        """Admit allowlisted exact retrieval or return an explicit denial."""
        request = {
            "skillId": skill_id,
            "version": version,
            "runtimeProfile": runtime_profile,
            "digest": digest,
        }
        spec = allowlist_spec(skill_id, version)
        reasons: list[str] = []
        if spec is None:
            reasons.append("release_not_selectable")
        elif spec.runtime_profile != runtime_profile:
            reasons.append("incompatible")
        lifecycle = _lifecycle_for(spec, self._matrix) if spec else ""
        if lifecycle == QUARANTINED:
            reasons.append("quarantined")
        release_id = f"{skill_id}@{version}"
        if self._availability.get(release_id) == REVOKED:
            reasons.append("withdrawn")
        if spec is not None and not reasons:
            try:
                record = self.retrieve_exact(skill_id, version, digest=digest)
            except PublicationError as exc:
                code = str(exc)
                if code == "digest_mismatch":
                    reasons.append("incompatible")
                elif code in {REVOKED, "withdrawn"}:
                    reasons.append("withdrawn")
                else:
                    reasons.append("release_not_selectable")
            else:
                if not record["skillsReleaseSelectability"]["status"]:
                    reasons.append("release_not_selectable")
                else:
                    return {
                        "request": request,
                        "denied": False,
                        "reasons": [],
                        "release": record,
                        "decision": "selectable",
                    }
        if not reasons:
            reasons.append("release_not_selectable")
        return {
            "request": request,
            "denied": True,
            "reasons": sorted(set(reasons)),
            "release": None,
            "decision": "ineligible",
        }

    def selectable_releases(self) -> list[dict[str, Any]]:
        """Return currently selectable allowlisted releases."""
        selected: list[dict[str, Any]] = []
        for spec in INITIAL_ALLOWLIST:
            record = self._records.get(spec.release_id)
            if record is None:
                continue
            if self._availability.get(spec.release_id) != AVAILABLE:
                continue
            if not record["skillsReleaseSelectability"]["status"]:
                continue
            selected.append(dict(record))
        return selected

    def ordinary_selectable_count(self) -> int:
        """Return the ordinary selectable count (never a catalogue aggregate)."""
        return len(self.selectable_releases())

    def intended_pointers(self) -> dict[str, str]:
        """Return intended internal channel pointers (not applied live)."""
        return dict(self._pointers)

    def revoke(self, skill_id: str, version: str) -> None:
        """Revoke one release and restore the prior intended pointer when needed."""
        release_id = f"{skill_id}@{version}"
        if release_id not in self._records:
            raise PublicationError("release_not_found")
        self._availability[release_id] = REVOKED
        record = self._records[release_id]
        record["availability"] = REVOKED
        record["skillsReleaseSelectability"] = _gate(
            status=False,
            evidence_ref=_opaque_ref("revoked", release_id),
        )
        if self._pointers.get(skill_id) == version:
            prior = None
            for item_skill, expected, new_version in reversed(self._pointer_history):
                if item_skill == skill_id and new_version == version:
                    prior = expected
                    break
            current = self._pointers.get(skill_id)
            try:
                if prior is None:
                    self._registry.clear_current(skill_id, current)
                    self._pointers.pop(skill_id, None)
                else:
                    self._registry.set_current(skill_id, prior, current)
                    self._pointers[skill_id] = prior
            except ReleaseError as exc:
                raise PublicationError(str(exc)) from exc

    def reinstate(self, skill_id: str, version: str) -> None:
        """Restore a previously published allowlisted release without live apply."""
        spec = allowlist_spec(skill_id, version)
        if spec is None:
            raise PublicationError("release_not_selectable")
        release_id = spec.release_id
        if release_id not in self._records:
            raise PublicationError("release_not_found")
        self._availability[release_id] = AVAILABLE
        record = self._records[release_id]
        record["availability"] = AVAILABLE
        record["skillsReleaseSelectability"] = _gate(
            status=True,
            evidence_ref=_opaque_ref("allowlist", release_id),
        )

    def rollback_pointer(self, skill_id: str, *, expected: str | None, version: str) -> None:
        """Atomically restore an intended pointer without rewriting release rows."""
        if self._pointers.get(skill_id) != expected:
            raise PublicationError("current_pointer_conflict")
        release_id = f"{skill_id}@{version}"
        if release_id not in self._records:
            raise PublicationError("release_not_found")
        if self._availability.get(release_id) != AVAILABLE:
            raise PublicationError(self._availability.get(release_id) or "unavailable")
        try:
            self._registry.set_current(skill_id, version, expected)
        except ReleaseError as exc:
            raise PublicationError(str(exc)) from exc
        self._pointers[skill_id] = version
        self._pointer_history.append((skill_id, expected, version))

    def denial_matrix(
        self,
        requests: Iterable[Mapping[str, str]],
    ) -> list[dict[str, Any]]:
        """Evaluate a closed set of ineligible or mixed profile requests."""
        rows: list[dict[str, Any]] = []
        for item in requests:
            rows.append(
                self.evaluate_request(
                    skill_id=str(item["skillId"]),
                    version=str(item["version"]),
                    runtime_profile=str(item.get("runtimeProfile") or ""),
                    digest=item.get("digest"),
                )
            )
        return rows

    def receipt(self, *, catalog_skill_count: int | None = None) -> dict[str, Any]:
        """Build the source-only publication receipt."""
        selectable = self.selectable_releases()
        payload = {
            "schemaVersion": SCHEMA_VERSION,
            "kind": PUBLICATION_KIND,
            "liveProviderMutation": False,
            "consumerConfiguration": False,
            "externalApply": False,
            "catalogExpansion": False,
            "intendedChannel": INTENDED_CHANNEL,
            "allowlist": [
                {
                    "skillId": item.skill_id,
                    "version": item.version,
                    "runtimeProfile": item.runtime_profile,
                    "releaseId": item.release_id,
                }
                for item in INITIAL_ALLOWLIST
            ],
            "ordinarySelectableCount": ORDINARY_SELECTABLE_COUNT,
            "selectableCount": len(selectable),
            "catalogSkillCount": catalog_skill_count,
            "releases": [self._records[item.release_id] for item in INITIAL_ALLOWLIST if item.release_id in self._records],
            "intendedPointers": self.intended_pointers(),
            "qualificationMatrixBound": bool(self._matrix),
        }
        payload["receiptDigest"] = sha256(payload)
        return payload


def catalog_skill_count(repo_root: str | Path) -> int:
    """Read the source catalogue skill_count without treating it as selectable."""
    index = Path(repo_root).resolve() / "catalog" / "index.json"
    data = json.loads(index.read_text(encoding="utf-8"))
    return int(data["skill_count"])


def load_qualification_matrix(path: str | Path | None) -> dict[str, Any] | None:
    """Load an ED-03 matrix JSON when the protected receipt path exists."""
    if path is None:
        return None
    matrix_path = Path(path)
    if not matrix_path.is_file():
        return None
    data = json.loads(matrix_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PublicationError("qualification_matrix_not_object")
    return data


def publish_exact_initial_releases(
    repo_root: str | Path,
    *,
    qualification_matrix: Mapping[str, Any] | None = None,
    catalog_count: int | None = None,
) -> tuple[SourceOnlyInitialPublisher, dict[str, Any]]:
    """Publish the frozen initial set and return the publisher plus receipt."""
    publisher = SourceOnlyInitialPublisher()
    counted = catalog_count
    if counted is None:
        index = Path(repo_root).resolve() / "catalog" / "index.json"
        if index.is_file():
            counted = catalog_skill_count(repo_root)
    receipt = publisher.publish_initial_set(
        repo_root,
        qualification_matrix=qualification_matrix,
        catalog_skill_count=counted,
    )
    return publisher, receipt


__all__ = [
    "ALLOWLIST_RELEASE_IDS",
    "INITIAL_ALLOWLIST",
    "InitialReleaseSpec",
    "ORDINARY_SELECTABLE_COUNT",
    "PublicationError",
    "SourceOnlyInitialPublisher",
    "catalog_skill_count",
    "collect_skill_files",
    "load_qualification_matrix",
    "publish_exact_initial_releases",
]
