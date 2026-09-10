"""Hash-bound LiNKskills production store migration package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_ID = "lskills-production-store-readiness"
PACKAGE_VERSION = "1.0.0"
APPLY_AUTHORITY = "LiNKplatform"
LIVE_RECOVERY_OWNER = "01a0843c-0df9-74e2-907a-05c5f736d6ed"
COMPATIBLE_POSTGRES_MAJOR = (17,)
MANIFEST_NAME = "MIGRATION-MANIFEST.json"

PAYLOAD_ENTRY_IDS = (
    "20260715_000002_lskills_catalog_core",
    "20260715_000003_lskills_catalog_seed",
    "20260718_000004_lskills_postgrest_exposure",
    "20260727_000005_lskills_registry_foundation",
    "20260728_000006_lskills_rls_actor_org_scope",
    "20260730_000007_lskills_gateway_persistence",
    "20260730_000008_lskills_review_queue",
    "20260730_000009_lskills_review_queue_actor_isolation",
    "20260803_000010_lskills_canary_echo_usable_seed",
    "20260804_000011_lskills_gateway_role_rls_contract",
    "20260824_000012_lskills_external_collection_lifecycle",
)

REQUIRED_RELATIONS = (
    "catalog",
    "telemetry",
    "eval_runs",
    "releases",
    "bundles",
    "fragments",
    "tools",
    "execution_profiles",
    "certifications",
    "skill_runs",
    "run_events",
    "feedback",
    "trace_to_eval_candidates",
    "idempotency",
    "side_effect_intents",
    "gateway_events",
    "review_queue",
    "external_vendor_releases",
    "external_collection_manifests",
    "external_adapted_releases",
    "external_update_candidates",
    "external_librarian_reviews",
    "external_current_pointers",
    "external_platform_receipts",
    "store_package",
)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's exact bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def persistence_root(repo_root: Path) -> Path:
    """Return ``packages/persistence`` under ``repo_root``."""
    return Path(repo_root) / "packages" / "persistence"


def manifest_path(repo_root: Path) -> Path:
    """Return the production store migration manifest path."""
    return persistence_root(repo_root) / MANIFEST_NAME


def load_manifest(repo_root: Path) -> dict[str, Any]:
    """Load the versioned Platform-consumable migration manifest."""
    payload = json.loads(manifest_path(repo_root).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("migration_manifest_invalid")
    return payload


def canonical_payload_bytes(manifest: Mapping[str, Any]) -> bytes:
    """Canonical bytes for the payload digest (000002–000012 only)."""
    by_id = {str(entry["id"]): entry for entry in manifest["entries"]}
    lines = [
        str(manifest["package_id"]),
        str(manifest["package_version"]),
        str(manifest["status"]),
        APPLY_AUTHORITY,
        ",".join(str(v) for v in manifest.get("compatible_postgres_major", [])),
    ]
    for entry_id in PAYLOAD_ENTRY_IDS:
        entry = by_id[entry_id]
        lines.append(
            f"{int(entry['order']):03d} {entry_id} {entry['up']} {entry['up_sha256']}"
        )
        if entry.get("down"):
            lines.append(
                f"{int(entry['order']):03d} down {entry['down']} {entry['down_sha256']}"
            )
    return ("\n".join(lines) + "\n").encode("utf-8")


def payload_digest(manifest: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical payload (excludes the 000013 binder file)."""
    return hashlib.sha256(canonical_payload_bytes(manifest)).hexdigest()


def canonical_package_bytes(manifest: Mapping[str, Any]) -> bytes:
    """Canonical bytes for the full package digest (all entries + payload digest)."""
    lines = [
        str(manifest["package_id"]),
        str(manifest["package_version"]),
        payload_digest(manifest),
    ]
    for entry in sorted(manifest["entries"], key=lambda item: int(item["order"])):
        lines.append(
            f"{int(entry['order']):03d} {entry['id']} {entry['up']} {entry['up_sha256']}"
        )
        if entry.get("down"):
            lines.append(
                f"{int(entry['order']):03d} down {entry['down']} {entry['down_sha256']}"
            )
    return ("\n".join(lines) + "\n").encode("utf-8")


def package_digest(manifest: Mapping[str, Any]) -> str:
    """SHA-256 of the full hash-bound package including the binder."""
    return hashlib.sha256(canonical_package_bytes(manifest)).hexdigest()


def verify_manifest_files(repo_root: Path, manifest: Mapping[str, Any] | None = None) -> dict[str, str]:
    """Fail closed when on-disk SQL bytes do not match pinned hashes."""
    data = dict(manifest or load_manifest(repo_root))
    root = Path(repo_root)
    mismatches: list[str] = []
    for entry in data["entries"]:
        for key in ("up", "down"):
            rel = entry.get(key)
            digest_key = f"{key}_sha256"
            if not rel:
                continue
            path = root / str(rel)
            if not path.is_file():
                mismatches.append(f"missing:{rel}")
                continue
            actual = sha256_file(path)
            expected = str(entry[digest_key])
            if actual != expected:
                mismatches.append(f"hash:{rel}")
    if mismatches:
        raise ValueError("migration_fingerprint_mismatch:" + ",".join(mismatches))
    expected_payload = str(data["payload_digest_sha256"])
    actual_payload = payload_digest(data)
    if expected_payload != actual_payload:
        raise ValueError("payload_digest_mismatch")
    expected_package = str(data["package_digest_sha256"])
    actual_package = package_digest(data)
    if expected_package != actual_package:
        raise ValueError("package_digest_mismatch")
    if data.get("package_id") != PACKAGE_ID:
        raise ValueError("package_id_mismatch")
    if data.get("apply_authority") != APPLY_AUTHORITY:
        raise ValueError("apply_authority_mismatch")
    if tuple(data.get("compatible_postgres_major") or ()) != COMPATIBLE_POSTGRES_MAJOR:
        raise ValueError("postgres_compatibility_mismatch")
    return {
        "payload_digest_sha256": actual_payload,
        "package_digest_sha256": actual_package,
    }
