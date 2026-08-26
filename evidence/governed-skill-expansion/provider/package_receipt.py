"""Content-addressed package and receipt identity helpers for local rehearsals.

These helpers operate only on supplied bytes and mappings. They never contact
a provider, inspect a hosted environment, or turn a digest into admission.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_IDENTITY_FIELDS = (
    "repository", "ref", "commit", "tree", "package_id", "package_version",
    "package_sha256", "manifest_sha256",
)
SOURCE_IDENTITY_FIELDS = ("repository", "ref", "commit", "tree")


class PackageIdentityError(ValueError):
    """Raised when a package or receipt identity is incomplete or invalid."""


def strip_origin_userinfo(value: Any) -> str:
    """Remove userinfo from a Git origin so receipts never store tokens."""

    origin = value.strip() if isinstance(value, str) else ""
    if origin.startswith("git@") and ":" in origin[4:]:
        host, path = origin[4:].split(":", 1)
        origin = f"ssh://{host}/{path}"
    if "://" in origin:
        scheme, remainder = origin.split("://", 1)
        slash = remainder.find("/")
        authority = remainder if slash < 0 else remainder[:slash]
        path = "" if slash < 0 else remainder[slash:]
        if "@" in authority:
            authority = authority.rsplit("@", 1)[1]
        origin = f"{scheme}://{authority}{path}"
    return origin


def normalize_origin(value: Any) -> str:
    """Normalize an origin while rejecting empty and host-only values."""

    origin = strip_origin_userinfo(value)
    if not origin or any(character.isspace() for character in origin):
        raise PackageIdentityError("origin_must_be_nonempty_and_whitespace_free")
    origin = origin.rstrip("/")
    if origin.endswith(".git"):
        origin = origin[:-4]
    if "://" in origin:
        scheme, remainder = origin.split("://", 1)
        origin = f"{scheme.lower()}://{remainder}"
    if "/" not in origin.split("://", 1)[-1]:
        raise PackageIdentityError("origin_must_include_repository_path")
    return origin


def sha256_bytes(value: bytes) -> str:
    """Return the lowercase SHA-256 digest of bytes."""

    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> bytes:
    """Encode JSON deterministically for receipt and fixture hashing."""

    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def digest_json(value: Any) -> str:
    """Return the lowercase SHA-256 digest of canonical JSON."""

    return sha256_bytes(canonical_json(value))


def package_identity(
    *, repository: str, ref: str, commit: str, tree: str, package_id: str,
    package_version: str, package_bytes: bytes, manifest: Mapping[str, Any],
) -> dict[str, str]:
    """Build and validate an exact source-and-package identity."""

    identity = {
        "repository": normalize_origin(repository), "ref": ref, "commit": commit, "tree": tree,
        "package_id": package_id, "package_version": package_version,
        "package_sha256": sha256_bytes(package_bytes),
        "manifest_sha256": digest_json(manifest),
    }
    validate_identity(identity)
    return identity


def validate_identity(identity: Mapping[str, Any]) -> None:
    """Fail closed unless every immutable identity field is valid."""

    missing = [field for field in REQUIRED_IDENTITY_FIELDS
               if not isinstance(identity.get(field), str) or not identity[field].strip()]
    if missing:
        raise PackageIdentityError("missing_identity_fields:" + ",".join(missing))
    for field in ("package_sha256", "manifest_sha256"):
        if not SHA256_RE.fullmatch(identity[field]):
            raise PackageIdentityError(f"invalid_{field}")
    for field in ("commit", "tree"):
        if not SHA40_RE.fullmatch(identity[field]):
            raise PackageIdentityError(f"invalid_{field}")
    if identity["ref"] in {"HEAD", "FETCH_HEAD"} or any(char.isspace() for char in identity["ref"]):
        raise PackageIdentityError("ambiguous_ref")
    try:
        normalize_origin(identity["repository"])
    except PackageIdentityError as exc:
        raise PackageIdentityError("invalid_repository") from exc


def _source_values(source: Mapping[str, Any]) -> dict[str, Any]:
    repository = source.get("repository", source.get("origin"))
    try:
        repository = normalize_origin(repository)
    except PackageIdentityError:
        pass
    return {"repository": repository, "ref": source.get("ref"),
            "commit": source.get("commit"), "tree": source.get("tree")}


def validate_source_binding(
    identity: Mapping[str, Any], checkout_identity: Mapping[str, Any],
    provider_identity: Mapping[str, Any],
) -> None:
    """Require package identity to match checkout and provider source."""

    expected = _source_values(identity)
    for label, source in (("checkout", checkout_identity), ("provider", provider_identity)):
        observed = _source_values(source)
        missing = [field for field in SOURCE_IDENTITY_FIELDS
                   if not isinstance(observed[field], str) or not observed[field].strip()]
        if missing:
            raise PackageIdentityError(f"{label}_identity_missing:" + ",".join(missing))
        mismatched = [field for field in SOURCE_IDENTITY_FIELDS if expected[field] != observed[field]]
        if mismatched:
            raise PackageIdentityError(f"{label}_identity_mismatch:" + ",".join(mismatched))


def bind_receipt(
    receipt: Mapping[str, Any], identity: Mapping[str, Any], *, result_digest: str,
    checkout_identity: Mapping[str, Any] | None = None,
    provider_identity: Mapping[str, Any] | None = None,
    receipt_ref: str = "opaque:pkt25:offline-provider-rehearsal",
) -> dict[str, Any]:
    """Attach exact package/source identity to a local-only receipt."""

    validate_identity(identity)
    if not SHA256_RE.fullmatch(result_digest):
        raise PackageIdentityError("invalid_result_digest")
    if not isinstance(receipt_ref, str) or not receipt_ref.strip() or any(char.isspace() for char in receipt_ref):
        raise PackageIdentityError("invalid_receipt_ref")
    if not receipt_ref.startswith("opaque:"):
        path = Path(receipt_ref)
        if path.is_absolute() or ".." in path.parts:
            raise PackageIdentityError("receipt_ref_must_be_relative_and_confined")
    checkout_identity = checkout_identity or identity
    provider_identity = provider_identity or identity
    validate_source_binding(identity, checkout_identity, provider_identity)
    bound = dict(receipt)
    bound["identity"] = dict(identity)
    bound["result_sha256"] = result_digest
    bound["receipt_ref"] = receipt_ref
    bound["identity_binding"] = {"status": "PASS", "fields": list(REQUIRED_IDENTITY_FIELDS),
                                  "source_only": True, "external_provider_contacted": False}
    bound["source_binding"] = {"status": "PASS", "fields": list(SOURCE_IDENTITY_FIELDS),
                                "checkout": _source_values(checkout_identity),
                                "provider": _source_values(provider_identity)}
    bound["receipt_digest"] = digest_json(bound)
    bound["receipt_sha256"] = bound["receipt_digest"]
    return bound
