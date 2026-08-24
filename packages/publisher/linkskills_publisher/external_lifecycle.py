"""Governed external collection, adaptation, and update lifecycle.

The lifecycle is deliberately provider-side and source-only.  It preserves the
exact bytes received from a vendor, records their lineage, and produces signed
update candidates for Librarian/Platform review.  Candidate delivery never
changes a current pointer; only a matching Platform apply receipt can do that.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence


class LifecycleError(ValueError):
    """Fail-closed error raised by the external lifecycle."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else _canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _require_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise LifecycleError(f"missing_{field_name}")
    return text


def _safe_path(path: Any) -> str:
    text = _require_text(path, "file_path")
    parts = text.split("/")
    if (
        "\x00" in text
        or "\\" in text
        or text.startswith("/")
        or text.endswith("/")
        or any(part in {"", ".", ".."} for part in parts)
        or (len(parts[0]) == 2 and parts[0][1] == ":")
    ):
        raise LifecycleError("unsafe_file_path")
    normalized = posixpath.normpath(text)
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise LifecycleError("unsafe_file_path")
    return normalized


def inventory_digest(files: Mapping[str, bytes]) -> str:
    """Return a deterministic digest of exact relative paths and byte content."""
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_path, body in sorted(files.items(), key=lambda item: str(item[0])):
        path = _safe_path(raw_path)
        folded = path.casefold()
        if folded in seen:
            raise LifecycleError("inventory_path_collision")
        seen.add(folded)
        if not isinstance(body, bytes):
            raise LifecycleError("invalid_file_body")
        entries.append({"path": path, "digest": _digest(body), "size": len(body)})
    return _digest(entries)


def _copy_files(files: Mapping[str, bytes]) -> dict[str, bytes]:
    copied: dict[str, bytes] = {}
    for path, body in files.items():
        normalized = _safe_path(path)
        if normalized in copied:
            raise LifecycleError("inventory_path_collision")
        if not isinstance(body, bytes):
            raise LifecycleError("invalid_file_body")
        copied[normalized] = bytes(body)
    if not copied:
        raise LifecycleError("empty_vendor_release")
    return copied


@dataclass(frozen=True)
class FileProvenance:
    """Immutable source and licence record for one vendor file."""

    path: str
    digest: str
    size: int
    source_path: str
    license_ref: str
    source_url: str = ""


@dataclass(frozen=True)
class VendorRelease:
    """Exact, unchanged vendor bytes and their provenance."""

    release_id: str
    collection_id: str
    vendor: str
    repository: str
    publisher: str
    license_ref: str
    source_ref: str
    source_path: str
    retrieved_at: str
    inventory_digest: str
    content_digest: str
    files: Mapping[str, bytes]
    file_provenance: tuple[FileProvenance, ...]
    lifecycle: str = "preserved"
    availability: str = "available"
    qualification: str = "unqualified"
    selectable: bool = False


@dataclass(frozen=True)
class CollectionManifest:
    """Immutable collection inventory binding releases to one source snapshot."""

    collection_id: str
    version: str
    release_ids: tuple[str, ...]
    inventory_digest: str
    source_release: str
    license_ref: str
    manifest_digest: str
    created_at: str


@dataclass(frozen=True)
class AdaptedRelease:
    """A separate release explicitly linked to an unchanged vendor release."""

    release_id: str
    collection_id: str
    base_vendor_release_id: str
    adaptation_ref: str
    adaptation_digest: str
    inventory_digest: str
    files: Mapping[str, bytes]
    file_provenance: tuple[FileProvenance, ...]
    lifecycle: str = "preserved"
    availability: str = "available"
    qualification: str = "unqualified"
    selectable: bool = False


@dataclass(frozen=True)
class UpdateCandidate:
    """Signed, idempotent proposal submitted for review."""

    candidate_id: str
    idempotency_key: str
    collection_id: str
    current_release_id: str | None
    proposed_release_id: str
    candidate_digest: str
    signature: str
    signer: str
    submitted_at: str
    status: str = "proposed"
    review_id: str | None = None
    platform_review_receipt_id: str | None = None
    platform_apply_receipt_id: str | None = None


@dataclass(frozen=True)
class ReviewOutcome:
    """Librarian recommendation backed by all required review dimensions."""

    review_id: str
    candidate_id: str
    outcome: str
    evidence: Mapping[str, Any]
    reviewer: str
    reviewed_at: str
    status: str


class ExternalCollectionLifecycle:
    """In-memory lifecycle reference implementation for source and tests.

    This class does not fetch external bytes, run imported content, apply SQL,
    or independently activate a release.  Platform receipts are the only
    boundary that can move a collection current pointer.
    """

    REVIEW_OUTCOMES = frozenset({"accept", "adapt", "postpone", "reject"})
    REVIEW_EVIDENCE = frozenset(
        {"diff", "license", "security", "compatibility", "evaluation", "customization", "feedback"}
    )

    def __init__(self) -> None:
        self.vendor_releases: dict[str, VendorRelease] = {}
        self.adapted_releases: dict[str, AdaptedRelease] = {}
        self.collections: dict[str, CollectionManifest] = {}
        self.candidates: dict[str, UpdateCandidate] = {}
        self._candidate_by_key: dict[str, str] = {}
        self.reviews: dict[str, ReviewOutcome] = {}
        self.platform_receipts: dict[str, dict[str, Any]] = {}
        self.current: dict[str, str | None] = {}
        self.pointer_history: list[dict[str, Any]] = []

    def ingest_vendor_release(
        self,
        collection_id: str,
        files: Mapping[str, bytes],
        *,
        vendor: str,
        repository: str,
        publisher: str,
        license_ref: str,
        source_ref: str,
        source_path: str = ".",
        retrieved_at: str | None = None,
        file_metadata: Mapping[str, Mapping[str, Any]] | None = None,
        availability: str = "available",
        qualification: str = "unqualified",
        release_id: str | None = None,
    ) -> VendorRelease:
        """Preserve vendor bytes with explicit per-file provenance/licence."""
        collection = _require_text(collection_id, "collection_id")
        vendor_name = _require_text(vendor, "vendor")
        repository_name = _require_text(repository, "repository")
        publisher_name = _require_text(publisher, "publisher")
        top_license = _require_text(license_ref, "license_ref")
        source = _require_text(source_ref, "source_ref")
        root_path = _require_text(source_path, "source_path")
        copied = _copy_files(files)
        inventory = inventory_digest(copied)
        rid = release_id or f"vendor:{collection}:{source}:{inventory.removeprefix('sha256:')[:16]}"
        rid = _require_text(rid, "release_id")
        metadata = file_metadata or {}
        provenance: list[FileProvenance] = []
        for path, body in sorted(copied.items()):
            details = dict(metadata.get(path) or metadata.get(str(path)) or {})
            provenance.append(
                FileProvenance(
                    path=path,
                    digest=_digest(body),
                    size=len(body),
                    source_path=_require_text(details.get("source_path") or f"{root_path}/{path}", "file_source_path"),
                    license_ref=_require_text(details.get("license_ref") or details.get("license") or top_license, "file_license_ref"),
                    source_url=str(details.get("source_url") or "").strip(),
                )
            )
        if rid in self.vendor_releases:
            existing = self.vendor_releases[rid]
            if existing.inventory_digest != inventory:
                raise LifecycleError("immutable_vendor_release_conflict")
            return existing
        release = VendorRelease(
            release_id=rid,
            collection_id=collection,
            vendor=vendor_name,
            repository=repository_name,
            publisher=publisher_name,
            license_ref=top_license,
            source_ref=source,
            source_path=root_path,
            retrieved_at=str(retrieved_at or _utc_now()),
            inventory_digest=inventory,
            content_digest=inventory,
            files=copied,
            file_provenance=tuple(provenance),
            availability=availability,
            qualification=qualification,
            selectable=qualification == "qualified" and availability == "available",
        )
        self.vendor_releases[rid] = release
        self.current.setdefault(collection, None)
        return release

    # Explicit alias used by callers that model ingestion as registration.
    register_vendor_release = ingest_vendor_release

    def create_collection_manifest(
        self,
        collection_id: str,
        version: str,
        release_ids: Sequence[str],
        *,
        source_release: str,
        license_ref: str,
    ) -> CollectionManifest:
        """Bind a deterministic collection inventory without activating it."""
        collection = _require_text(collection_id, "collection_id")
        release_tuple = tuple(dict.fromkeys(_require_text(item, "release_id") for item in release_ids))
        if not release_tuple:
            raise LifecycleError("empty_collection_manifest")
        for release_id in release_tuple:
            if release_id not in self.vendor_releases and release_id not in self.adapted_releases:
                raise LifecycleError("manifest_release_not_found")
            release = self.vendor_releases.get(release_id) or self.adapted_releases.get(release_id)
            if release is None or release.collection_id != collection:
                raise LifecycleError("manifest_release_collection_mismatch")
        payload = {
            "collection_id": collection,
            "version": _require_text(version, "version"),
            "release_ids": release_tuple,
            "source_release": _require_text(source_release, "source_release"),
            "license_ref": _require_text(license_ref, "license_ref"),
        }
        digest = _digest(payload)
        manifest = CollectionManifest(
            collection_id=collection,
            version=payload["version"],
            release_ids=release_tuple,
            inventory_digest=_digest([self.release_inventory_digest(item) for item in release_tuple]),
            source_release=payload["source_release"],
            license_ref=payload["license_ref"],
            manifest_digest=digest,
            created_at=_utc_now(),
        )
        key = f"{collection}@{manifest.version}"
        existing = self.collections.get(key)
        if existing is not None and existing.manifest_digest != digest:
            raise LifecycleError("immutable_collection_manifest_conflict")
        self.collections[key] = existing or manifest
        self.current.setdefault(collection, None)
        return existing or manifest

    def register_adaptation(
        self,
        collection_id: str,
        base_vendor_release_id: str,
        files: Mapping[str, bytes],
        *,
        adaptation_ref: str,
        file_metadata: Mapping[str, Mapping[str, Any]] | None = None,
        qualification: str = "unqualified",
        selectable: bool = False,
        release_id: str | None = None,
    ) -> AdaptedRelease:
        """Store a separate adapted release linked to its vendor original."""
        collection = _require_text(collection_id, "collection_id")
        base = self.vendor_releases.get(base_vendor_release_id)
        if base is None:
            raise LifecycleError("base_vendor_release_not_found")
        if base.collection_id != collection:
            raise LifecycleError("base_vendor_collection_mismatch")
        copied = _copy_files(files)
        inventory = inventory_digest(copied)
        adaptation_digest = _digest(
            {"base_vendor_release_id": base_vendor_release_id, "adaptation_ref": adaptation_ref, "inventory_digest": inventory}
        )
        rid = _require_text(release_id or f"adaptation:{collection}:{adaptation_digest.removeprefix('sha256:')[:20]}", "release_id")
        metadata = file_metadata or {}
        provenance = tuple(
            FileProvenance(
                path=path,
                digest=_digest(body),
                size=len(body),
                source_path=str((metadata.get(path) or {}).get("source_path") or f"adaptation:{adaptation_ref}/{path}"),
                license_ref=str((metadata.get(path) or {}).get("license_ref") or base.license_ref),
                source_url=str((metadata.get(path) or {}).get("source_url") or ""),
            )
            for path, body in sorted(copied.items())
        )
        if any(not item.source_path.strip() or not item.license_ref.strip() for item in provenance):
            raise LifecycleError("missing_adaptation_provenance")
        existing = self.adapted_releases.get(rid)
        if existing is not None:
            if existing.inventory_digest != inventory or existing.base_vendor_release_id != base_vendor_release_id:
                raise LifecycleError("immutable_adaptation_conflict")
            return existing
        adapted = AdaptedRelease(
            release_id=rid,
            collection_id=collection,
            base_vendor_release_id=base_vendor_release_id,
            adaptation_ref=_require_text(adaptation_ref, "adaptation_ref"),
            adaptation_digest=adaptation_digest,
            inventory_digest=inventory,
            files=copied,
            file_provenance=provenance,
            qualification=qualification,
            selectable=bool(selectable and qualification == "qualified"),
        )
        self.adapted_releases[rid] = adapted
        self.current.setdefault(adapted.collection_id, None)
        return adapted

    def release_inventory_digest(self, release_id: str) -> str:
        """Return the immutable inventory digest for a vendor or adapted release."""
        if release_id in self.vendor_releases:
            return self.vendor_releases[release_id].inventory_digest
        if release_id in self.adapted_releases:
            return self.adapted_releases[release_id].inventory_digest
        raise LifecycleError("release_not_found")

    def submit_update_candidate(
        self,
        collection_id: str,
        proposed_release_id: str,
        *,
        idempotency_key: str,
        signature: str,
        signer: str,
        current_release_id: str | None = None,
        candidate_id: str | None = None,
        verify_signature: Callable[[str, str, str], bool] | None = None,
    ) -> UpdateCandidate:
        """Accept a signed candidate exactly once; never switch current state."""
        collection = _require_text(collection_id, "collection_id")
        key = _require_text(idempotency_key, "idempotency_key")
        sig = _require_text(signature, "signature")
        signer_name = _require_text(signer, "signer")
        if proposed_release_id not in self.vendor_releases and proposed_release_id not in self.adapted_releases:
            raise LifecycleError("candidate_release_not_found")
        proposed = self.vendor_releases.get(proposed_release_id) or self.adapted_releases.get(proposed_release_id)
        if proposed is None or proposed.collection_id != collection:
            raise LifecycleError("candidate_release_collection_mismatch")
        effective_current = self.current.get(collection) if current_release_id is None else current_release_id
        if effective_current is not None:
            current = self.vendor_releases.get(effective_current) or self.adapted_releases.get(effective_current)
            if current is None:
                raise LifecycleError("candidate_current_release_not_found")
            if current.collection_id != collection:
                raise LifecycleError("candidate_current_collection_mismatch")
        payload = {
            "collection_id": collection,
            "current_release_id": effective_current,
            "proposed_release_id": proposed_release_id,
            "idempotency_key": key,
            "signer": signer_name,
        }
        candidate_digest = _digest(payload)
        if verify_signature is None:
            raise LifecycleError("candidate_signature_verifier_required")
        try:
            verified = verify_signature(signer_name, candidate_digest, sig)
        except Exception as exc:  # verifier failures fail closed without details
            raise LifecycleError("candidate_signature_invalid") from exc
        if verified is not True:
            raise LifecycleError("candidate_signature_invalid")
        existing_id = self._candidate_by_key.get(key)
        if existing_id is not None:
            existing = self.candidates[existing_id]
            if existing.candidate_digest != candidate_digest or existing.signature != sig:
                raise LifecycleError("idempotency_conflict")
            return existing
        cid = _require_text(candidate_id or f"candidate:{candidate_digest.removeprefix('sha256:')[:24]}", "candidate_id")
        if cid in self.candidates:
            raise LifecycleError("candidate_id_conflict")
        candidate = UpdateCandidate(
            candidate_id=cid,
            idempotency_key=key,
            collection_id=collection,
            current_release_id=effective_current,
            proposed_release_id=proposed_release_id,
            candidate_digest=candidate_digest,
            signature=sig,
            signer=signer_name,
            submitted_at=_utc_now(),
        )
        self.candidates[cid] = candidate
        self._candidate_by_key[key] = cid
        return candidate

    def review_candidate(
        self,
        candidate_id: str,
        outcome: str,
        evidence: Mapping[str, Any],
        *,
        reviewer: str,
        review_id: str | None = None,
    ) -> ReviewOutcome:
        """Record one Librarian outcome without qualifying or promoting bytes."""
        candidate = self.candidates.get(candidate_id)
        if candidate is None:
            raise LifecycleError("candidate_not_found")
        decision = _require_text(outcome, "review_outcome").lower()
        if decision not in self.REVIEW_OUTCOMES:
            raise LifecycleError("invalid_review_outcome")
        missing = sorted(self.REVIEW_EVIDENCE.difference(evidence))
        if missing:
            raise LifecycleError("missing_review_evidence:" + ",".join(missing))
        rid = _require_text(review_id or f"review:{candidate_id}", "review_id")
        status = {
            "accept": "accepted_pending_platform",
            "adapt": "adaptation_pending_platform",
            "postpone": "postponed",
            "reject": "rejected",
        }[decision]
        reviewer_name = _require_text(reviewer, "reviewer")
        existing = self.reviews.get(rid)
        if existing is not None:
            if (existing.candidate_id, existing.outcome, dict(existing.evidence), existing.reviewer) != (
                candidate_id, decision, dict(evidence), reviewer_name
            ):
                raise LifecycleError("immutable_review_conflict")
            return existing
        review = ReviewOutcome(rid, candidate_id, decision, dict(evidence), reviewer_name, _utc_now(), status)
        self.reviews[rid] = review
        self.candidates[candidate_id] = UpdateCandidate(**{**candidate.__dict__, "status": status, "review_id": rid})
        return existing or review

    def record_platform_review_receipt(self, candidate_id: str, receipt: Mapping[str, Any]) -> Mapping[str, Any]:
        """Record Platform's review receipt; this is not an apply operation."""
        candidate = self.candidates.get(candidate_id)
        if candidate is None:
            raise LifecycleError("candidate_not_found")
        data = dict(receipt)
        receipt_id = _require_text(data.get("receipt_id"), "platform_review_receipt_id")
        if str(data.get("authority") or "") != "LiNKplatform":
            raise LifecycleError("platform_authority_required")
        if str(data.get("candidate_digest") or "") != candidate.candidate_digest:
            raise LifecycleError("platform_review_candidate_mismatch")
        if str(data.get("decision") or "") not in self.REVIEW_OUTCOMES:
            raise LifecycleError("platform_review_decision_invalid")
        if candidate.review_id is None or self.reviews.get(candidate.review_id) is None:
            raise LifecycleError("librarian_review_required")
        if str(data.get("decision")) != self.reviews[candidate.review_id].outcome:
            raise LifecycleError("platform_review_decision_mismatch")
        data["candidate_id"] = candidate_id
        data["receipt_id"] = receipt_id
        self.platform_receipts[receipt_id] = data
        self.candidates[candidate_id] = UpdateCandidate(**{**candidate.__dict__, "platform_review_receipt_id": receipt_id})
        return dict(data)

    def record_platform_apply_receipt(
        self,
        candidate_id: str,
        receipt: Mapping[str, Any],
        *,
        expected_current: str | None = None,
    ) -> Mapping[str, Any]:
        """Apply a Platform receipt atomically to the local current-pointer record."""
        candidate = self.candidates.get(candidate_id)
        if candidate is None:
            raise LifecycleError("candidate_not_found")
        review = self.reviews.get(candidate.review_id or "")
        data = dict(receipt)
        receipt_id = _require_text(data.get("receipt_id"), "platform_apply_receipt_id")
        if str(data.get("authority") or "") != "LiNKplatform":
            raise LifecycleError("platform_authority_required")
        if not bool(data.get("applied")):
            raise LifecycleError("platform_apply_not_confirmed")
        if data.get("operation") == "rollback":
            raise LifecycleError("apply_receipt_operation_invalid")
        if data.get("operation") not in (None, "apply"):
            raise LifecycleError("apply_receipt_operation_invalid")
        data["operation"] = "apply"
        if str(data.get("candidate_digest") or "") != candidate.candidate_digest:
            raise LifecycleError("platform_apply_candidate_mismatch")
        if review is None or review.outcome not in {"accept", "adapt"}:
            raise LifecycleError("candidate_not_approved")
        if not candidate.platform_review_receipt_id or candidate.platform_review_receipt_id not in self.platform_receipts:
            raise LifecycleError("platform_review_receipt_required")
        target = str(data.get("release_id") or candidate.proposed_release_id)
        if target != candidate.proposed_release_id:
            raise LifecycleError("platform_apply_release_mismatch")
        target_record = self.vendor_releases.get(target) or self.adapted_releases.get(target)
        if target_record is None or not target_record.selectable:
            raise LifecycleError("release_not_selectable")
        collection = candidate.collection_id
        if target_record.collection_id != collection:
            raise LifecycleError("apply_release_collection_mismatch")
        if data.get("collection_id") not in (None, collection):
            raise LifecycleError("apply_collection_mismatch")
        existing_receipt = self.platform_receipts.get(receipt_id)
        if existing_receipt is not None:
            if any(
                existing_receipt.get(key) != value
                for key, value in {
                    "candidate_id": candidate_id,
                    "candidate_digest": candidate.candidate_digest,
                    "release_id": target,
                    "collection_id": collection,
                    "operation": "apply",
                }.items()
            ):
                raise LifecycleError("platform_receipt_conflict")
            return dict(existing_receipt)
        if candidate.platform_apply_receipt_id is not None:
            raise LifecycleError("platform_apply_already_recorded")
        current = self.current.get(collection)
        if expected_current is not None and current != expected_current:
            raise LifecycleError("current_pointer_conflict")
        data.update({"candidate_id": candidate_id, "receipt_id": receipt_id, "release_id": target, "collection_id": collection})
        self.platform_receipts[receipt_id] = data
        self.current[collection] = target
        self.pointer_history.append({"collection_id": collection, "from": current, "to": target, "receipt_id": receipt_id})
        self.candidates[candidate_id] = UpdateCandidate(**{**candidate.__dict__, "status": "applied", "platform_apply_receipt_id": receipt_id})
        return dict(data)

    def apply_candidate(self, candidate_id: str) -> None:
        """Reject every independent apply attempt; Platform owns live apply."""
        raise LifecycleError("platform_apply_receipt_required")

    def rollback_current(
        self,
        collection_id: str,
        target_release_id: str,
        *,
        expected_current: str | None,
        platform_receipt: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Restore a prior pointer only with an explicit Platform rollback receipt."""
        if target_release_id not in self.vendor_releases and target_release_id not in self.adapted_releases:
            raise LifecycleError("rollback_release_not_found")
        target_record = self.vendor_releases.get(target_release_id) or self.adapted_releases.get(target_release_id)
        if target_record is None or not target_record.selectable:
            raise LifecycleError("rollback_release_not_selectable")
        collection = _require_text(collection_id, "collection_id")
        if target_record.collection_id != collection:
            raise LifecycleError("rollback_release_collection_mismatch")
        receipt = dict(platform_receipt)
        if receipt.get("operation") != "rollback":
            raise LifecycleError("rollback_receipt_required")
        if receipt.get("authority") != "LiNKplatform" or not receipt.get("applied"):
            raise LifecycleError("platform_authority_required")
        if receipt.get("release_id") != target_release_id:
            raise LifecycleError("rollback_release_mismatch")
        if receipt.get("collection_id") not in (None, collection):
            raise LifecycleError("rollback_collection_mismatch")
        receipt["collection_id"] = collection
        receipt_id = _require_text(receipt.get("receipt_id"), "platform_apply_receipt_id")
        existing_receipt = self.platform_receipts.get(receipt_id)
        if existing_receipt is not None:
            if existing_receipt != receipt:
                raise LifecycleError("platform_receipt_conflict")
            return dict(existing_receipt)
        current = self.current.get(collection)
        if current != expected_current:
            raise LifecycleError("current_pointer_conflict")
        self.platform_receipts[receipt_id] = receipt
        self.current[collection_id] = target_release_id
        self.pointer_history.append({"collection_id": collection_id, "from": current, "to": target_release_id, "receipt_id": receipt_id, "rollback": True})
        return dict(receipt)

    def current_release(self, collection_id: str) -> str | None:
        """Read the current pointer without selecting a fallback release."""
        return self.current.get(collection_id)
