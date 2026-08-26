"""Fail-closed source validator for PKT-22 role-pack references.

The validator checks only repository-owned manifest, release, eligibility,
qualification, and runtime-profile metadata.  It does not qualify releases,
activate consumers, contact a provider, or infer hosted/VPS/E2E/production
evidence.  A role-pack file being present or schema-valid is therefore
insufficient for admission: every exact reference must resolve to a qualified
and selectable release plus an eligible intersection of the independent gates.
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
_QUALIFIED_STATUSES = frozenset({"qualified", "certified"})
_NONSELECTABLE_LIFECYCLES = frozenset(
    {
        "deprecated",
        "retired",
        "superseded",
        "withdrawn",
        "quarantined",
        "rejected",
        "incompatible",
        "unqualified",
        "draft",
        "eval_pending",
        "usable",
        "published",
    }
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


def _declared_profiles(value: Any) -> tuple[str, ...]:
    """Return declared runtime/execution profiles without inventing a wildcard."""

    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(sorted({item.strip() for item in value if isinstance(item, str) and item.strip()}))
    return ()


def _release_source_commit(release: Mapping[str, Any]) -> str:
    """Copy the exact source commit from provenance, never synthesizing one."""

    provenance = release.get("provenance")
    if isinstance(provenance, Mapping):
        commit = provenance.get("source_commit")
        if isinstance(commit, str) and commit:
            return commit
    commit = release.get("source_commit")
    return commit if isinstance(commit, str) else ""


def _release_profiles(release: Mapping[str, Any]) -> tuple[str, ...]:
    """Prefer execution_profiles, then compatible/runtime aliases if present."""

    for field in ("execution_profiles", "compatible_runtime_profiles", "runtime_profiles"):
        profiles = _declared_profiles(release.get(field))
        if profiles:
            return profiles
    return ()


def _qualification_status(record: Mapping[str, Any]) -> str:
    nested = record.get("qualification")
    if isinstance(nested, Mapping):
        status = nested.get("status")
        if isinstance(status, str) and status.strip():
            return status.strip().lower()
    status = record.get("status")
    return status.strip().lower() if isinstance(status, str) else ""


def validate_role_pack(
    manifest: Mapping[str, Any],
    releases: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    eligibilities: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    qualifications: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate one role pack and return a deterministic source-only receipt.

    ``admitted`` is true only when the supplied records independently prove
    every exact reference.  Missing, malformed, unqualified, unselectable,
    incompatible, or mismatched records always produce ``HOLD``; no fallback
    or substitution is attempted.  Source-only proof never invents
    qualification, provider, consumer, stage, VPS, or production evidence.
    """

    violations: list[dict[str, str]] = []
    schema_result = validate_instance(manifest, "role-pack-manifest-v0.1")
    for schema_error in schema_result.errors:
        violations.append(_error("manifest_schema_invalid", schema_error.path, schema_error.message))

    if qualifications is None:
        qualifications = ()
    release_index = _records_by_field(releases, "release_id")
    eligibility_index = _records_by_field(eligibilities, "eligibility_id")
    qualification_index = _records_by_field(qualifications, "release_id")
    violations.extend(
        _conflicting_duplicate_identity_violations(releases, "release_id", "release")
    )
    violations.extend(
        _conflicting_duplicate_identity_violations(eligibilities, "eligibility_id", "eligibility")
    )
    violations.extend(
        _conflicting_duplicate_identity_violations(qualifications, "release_id", "qualification")
    )
    refs = manifest.get("release_refs") if isinstance(manifest, Mapping) else None

    if not isinstance(refs, list):
        refs = []

    compatibility = manifest.get("compatibility") if isinstance(manifest, Mapping) else None
    manifest_profiles = _declared_profiles(
        compatibility.get("runtime_profiles") if isinstance(compatibility, Mapping) else None
    )

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

        lifecycle = release.get("lifecycle_state")
        lifecycle_qualified = lifecycle == "qualified"
        if not lifecycle_qualified:
            violations.append(_error("release_not_qualified", f"{path}.release_id", "only lifecycle_state=qualified may be referenced"))

        qualification_evidence_admits = False
        qualification = qualification_index.get(release_id)
        if qualification is None:
            violations.append(_error("qualification_evidence_missing", f"{path}.release_id", "independent qualification evidence is required and is not inferred from lifecycle_state"))
        else:
            qualification_identity_ok = True
            qualification_release_id = qualification.get("release_id")
            qualification_digest = qualification.get("bundle_hash") or qualification.get("result_digest")
            qualification_commit = qualification.get("source_commit")
            nested = qualification.get("qualification")
            if isinstance(nested, Mapping):
                qualification_digest = qualification_digest or nested.get("result_digest") or nested.get("bundle_hash")
                qualification_commit = qualification_commit or nested.get("source_commit")
                nested_release_id = nested.get("release_id")
                if nested_release_id not in {None, "", release_id}:
                    qualification_identity_ok = False
                    violations.append(_error("qualification_identity_mismatch", f"{path}.release_id", "nested qualification identity does not equal the exact release"))
            if qualification_release_id != release_id:
                qualification_identity_ok = False
                violations.append(_error("qualification_identity_mismatch", f"{path}.release_id", "qualification record is bound to a different release"))
            if qualification_digest != release.get("bundle_hash"):
                qualification_identity_ok = False
                violations.append(_error("qualification_identity_mismatch", f"{path}.release_id", "qualification digest does not equal the immutable release bundle hash"))
            release_commit = _release_source_commit(release)
            if not isinstance(qualification_commit, str) or not qualification_commit or qualification_commit != release_commit:
                qualification_identity_ok = False
                violations.append(_error("qualification_identity_mismatch", f"{path}.release_id", "qualification source_commit does not equal the exact release source commit"))
            qualification_status_ok = _qualification_status(qualification) in _QUALIFIED_STATUSES
            if not qualification_status_ok:
                violations.append(_error("release_not_qualified", f"{path}.release_id", "qualification status is not qualified or certified"))
            qualification_evidence_admits = qualification_identity_ok and qualification_status_ok

        release_profiles = _release_profiles(release)
        profile_selectable = bool(manifest_profiles) and bool(release_profiles) and bool(set(manifest_profiles).intersection(release_profiles))
        if not profile_selectable:
            violations.append(_error("incompatible_runtime_profile", f"{path}.release_id", "role-pack runtime profiles do not intersect exact release execution profiles"))

        selectability_gate = None
        if isinstance(eligibility_ref, str) and eligibility_ref:
            eligibility_preview = next(
                (
                    eligibility_index.get(candidate)
                    for candidate in _eligibility_candidates(eligibility_ref)
                    if eligibility_index.get(candidate) is not None
                ),
                None,
            )
            if isinstance(eligibility_preview, Mapping):
                selectability_gate = eligibility_preview.get("skills_release_selectability")
        selectability_true = isinstance(selectability_gate, Mapping) and selectability_gate.get("status") is True
        # Conjunction of independent gates: missing qualification evidence cannot
        # be rescued by lifecycle_state, profile intersection, or the selectability flag.
        if (
            not qualification_evidence_admits
            or not lifecycle_qualified
            or lifecycle in _NONSELECTABLE_LIFECYCLES
            or not profile_selectable
            or not selectability_true
        ):
            violations.append(
                _error(
                    "release_not_selectable",
                    f"{path}.release_id",
                    "lifecycle, qualification, runtime profile, and skills_release_selectability must all admit the exact release",
                )
            )

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
        "claims": {
            "qualified_release": False,
            "qualification_admission": False,
            "selectability": False,
            "activation": False,
            "provider_live": False,
            "consumer": False,
            "hosted_stage": False,
            "vps": False,
            "e2e": False,
            "production": False,
        },
    }


def load_role_pack_inputs(
    manifest_path: str | Path,
    release_directory: str | Path,
    eligibility_directory: str | Path,
    qualification_directory: str | Path | None = None,
) -> dict[str, Any]:
    """Load JSON metadata and validate it without mutating the repository."""

    def read(path: Path) -> Mapping[str, Any]:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, Mapping):
            raise ValueError(f"metadata must be an object: {path}")
        return value

    def read_dir(directory: Path) -> list[Mapping[str, Any]]:
        if not directory.is_dir():
            return []
        return [read(path) for path in sorted(directory.glob("*.json"))]

    manifest = read(Path(manifest_path))
    releases = read_dir(Path(release_directory))
    eligibilities = read_dir(Path(eligibility_directory))
    if qualification_directory is None:
        qualification_directory = Path(release_directory).parent / "qualifications"
    qualifications = read_dir(Path(qualification_directory))
    return validate_role_pack(manifest, releases, eligibilities, qualifications)
