"""Fail-closed source validator for PKT-22 role-pack references.

The validator checks only repository-owned manifest, release, and eligibility
metadata.  It does not qualify releases, activate consumers, contact a
provider, or infer hosted/VPS/E2E/production evidence.  A role-pack file being
present or schema-valid is therefore insufficient for admission: every exact
reference must resolve to a qualified release and an eligible intersection of
the independent gates.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_CONTRACTS = _ROOT / "packages" / "contracts"
if str(_CONTRACTS) not in sys.path:
    sys.path.insert(0, str(_CONTRACTS))

from linkskills_contracts import validate_instance  # noqa: E402


_ELIGIBILITY_GATES = (
    "platform_technical_eligibility",
    "skills_release_selectability",
    "consumer_profile_activation",
    "consumer_tool_authority",
)


def _record_entries(records: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> tuple[tuple[str, Mapping[str, Any]], ...]:
    """Return metadata records with stable labels, ignoring malformed entries."""

    if not isinstance(records, Mapping) and not isinstance(records, Sequence):
        return ()
    if isinstance(records, (str, bytes, bytearray)):
        return ()

    if isinstance(records, Mapping):
        return tuple((str(key), value) for key, value in records.items() if isinstance(value, Mapping))
    return tuple(("", value) for value in records if isinstance(value, Mapping))


def _records_by_field(records: Mapping[str, Any] | Sequence[Mapping[str, Any]], field: str) -> dict[str, Mapping[str, Any]]:
    """Index records by their declared identity without inventing one."""

    indexed: dict[str, Mapping[str, Any]] = {}
    for supplied_key, record in _record_entries(records):
        identity = record.get(field)
        if isinstance(identity, str) and identity:
            indexed.setdefault(identity, record)
        if supplied_key:
            indexed.setdefault(supplied_key, record)
    return indexed


def _conflicting_duplicate_identity_violations(
    records: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    field: str,
    kind: str,
) -> list[dict[str, str]]:
    """Reject an identity that resolves to multiple distinct metadata records."""

    by_identity: dict[str, list[Mapping[str, Any]]] = {}
    for _, record in _record_entries(records):
        identity = record.get(field)
        if isinstance(identity, str) and identity:
            by_identity.setdefault(identity, []).append(record)

    violations: list[dict[str, str]] = []
    for identity, candidates in by_identity.items():
        distinct: list[Mapping[str, Any]] = []
        for candidate in candidates:
            if not any(candidate == existing for existing in distinct):
                distinct.append(candidate)
        if len(distinct) > 1:
            violations.append(
                _error(
                    f"conflicting_duplicate_{kind}_identity",
                    f"$.{kind}s[{identity}]",
                    f"multiple distinct records declare the same {field}: {identity}",
                )
            )
    return violations


def _eligibility_candidates(reference: str) -> tuple[str, ...]:
    """Return only equivalent declared forms of an eligibility reference."""

    prefix = "opaque:eligibility:"
    if reference.startswith(prefix):
        return (reference, reference[len(prefix) :])
    return (reference,)


def _error(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def validate_role_pack(
    manifest: Mapping[str, Any],
    releases: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    eligibilities: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate one role pack and return a deterministic source-only receipt.

    ``admitted`` is true only when the supplied records independently prove
    every exact reference.  Missing, malformed, unqualified, incompatible,
    or mismatched records always produce ``HOLD``; no fallback or substitution
    is attempted.
    """

    violations: list[dict[str, str]] = []
    schema_result = validate_instance(manifest, "role-pack-manifest-v0.1")
    for schema_error in schema_result.errors:
        violations.append(_error("manifest_schema_invalid", schema_error.path, schema_error.message))

    release_index = _records_by_field(releases, "release_id")
    eligibility_index = _records_by_field(eligibilities, "eligibility_id")
    violations.extend(
        _conflicting_duplicate_identity_violations(releases, "release_id", "release")
    )
    violations.extend(
        _conflicting_duplicate_identity_violations(eligibilities, "eligibility_id", "eligibility")
    )
    refs = manifest.get("release_refs") if isinstance(manifest, Mapping) else None

    if not isinstance(refs, list):
        refs = []

    # Structural schema errors already make admission impossible, but these
    # checks remain bounded and useful for a precise contradiction receipt.
    if isinstance(manifest, Mapping):
        activation = manifest.get("activation")
        if isinstance(activation, Mapping) and activation.get("enabled") is not False:
            violations.append(_error("activation_must_remain_disabled", "$.activation.enabled", "role packs cannot activate agents or consumers"))
        if isinstance(activation, Mapping) and activation.get("activation_owner") != "consumer":
            violations.append(_error("activation_owner_must_be_consumer", "$.activation.activation_owner", "activation remains outside LiNKskills authority"))

    for index, reference in enumerate(refs):
        path = f"$.release_refs[{index}]"
        if not isinstance(reference, Mapping):
            violations.append(_error("release_reference_malformed", path, "reference must be an object"))
            continue
        release_id = reference.get("release_id")
        artifact_digest = reference.get("artifact_digest")
        eligibility_ref = reference.get("eligibility_ref")
        if not isinstance(release_id, str) or not release_id:
            violations.append(_error("release_identity_missing", f"{path}.release_id", "exact release_id is required"))
            continue
        release = release_index.get(release_id)
        if release is None:
            violations.append(_error("release_missing", f"{path}.release_id", f"no exact release record for {release_id}"))
            continue

        release_schema = validate_instance(release, "release-record-v0.1")
        for schema_error in release_schema.errors:
            violations.append(_error("release_schema_invalid", f"{path}.release_id{schema_error.path[1:]}", schema_error.message))

        if release.get("release_id") != release_id:
            violations.append(_error("release_identity_mismatch", f"{path}.release_id", "record identity does not equal manifest identity"))
        if artifact_digest != release.get("bundle_hash"):
            violations.append(_error("artifact_digest_mismatch", f"{path}.artifact_digest", "manifest digest does not equal the immutable release bundle hash"))
        if release.get("lifecycle_state") != "qualified":
            violations.append(_error("release_not_qualified", f"{path}.release_id", "only lifecycle_state=qualified may be referenced"))
        if not isinstance(eligibility_ref, str) or not eligibility_ref:
            violations.append(_error("eligibility_reference_missing", f"{path}.eligibility_ref", "exact eligibility reference is required"))
            continue
        if release.get("eligibility_ref") != eligibility_ref:
            violations.append(_error("release_eligibility_mismatch", f"{path}.eligibility_ref", "manifest and release eligibility references differ"))

        eligibility = next((eligibility_index.get(candidate) for candidate in _eligibility_candidates(eligibility_ref) if eligibility_index.get(candidate) is not None), None)
        if eligibility is None:
            violations.append(_error("eligibility_missing", f"{path}.eligibility_ref", f"no exact eligibility record for {eligibility_ref}"))
            continue
        eligibility_schema = validate_instance(eligibility, "eligibility-metadata-v0.1")
        for schema_error in eligibility_schema.errors:
            violations.append(_error("eligibility_schema_invalid", f"{path}.eligibility_ref{schema_error.path[1:]}", schema_error.message))
        if eligibility.get("release_id") != release_id:
            violations.append(_error("eligibility_release_mismatch", f"{path}.eligibility_ref", "eligibility record is bound to a different release"))
        if eligibility.get("decision") != "eligible":
            violations.append(_error("eligibility_not_eligible", f"{path}.eligibility_ref", "all independent eligibility gates must admit the exact release"))
        for gate in _ELIGIBILITY_GATES:
            gate_value = eligibility.get(gate)
            if not isinstance(gate_value, Mapping) or gate_value.get("status") is not True:
                violations.append(_error("eligibility_gate_not_satisfied", f"{path}.eligibility_ref.{gate}", "eligibility gate is absent or false"))

    violations.sort(key=lambda item: (item["path"], item["code"], item["detail"]))
    admitted = not violations and schema_result.ok and bool(refs)
    return {
        "schema_version": "0.1",
        "packet": "PKT-22",
        "status": "VALID" if admitted else "HOLD",
        "admitted": admitted,
        "role_pack_id": manifest.get("role_pack_id") if isinstance(manifest, Mapping) else None,
        "release_reference_count": len(refs),
        "proof_scope": "source",
        "violations": violations,
    }


def load_role_pack_inputs(
    manifest_path: str | Path,
    release_directory: str | Path,
    eligibility_directory: str | Path,
) -> dict[str, Any]:
    """Load JSON metadata and validate it without mutating the repository."""

    def read(path: Path) -> Mapping[str, Any]:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, Mapping):
            raise ValueError(f"metadata must be an object: {path}")
        return value

    manifest = read(Path(manifest_path))
    releases = [read(path) for path in sorted(Path(release_directory).glob("*.json"))]
    eligibilities = [read(path) for path in sorted(Path(eligibility_directory).glob("*.json"))]
    return validate_role_pack(manifest, releases, eligibilities)
