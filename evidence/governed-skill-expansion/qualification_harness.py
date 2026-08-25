"""Deterministic, fail-closed preparation for PKT-23 qualification evidence.

This module is deliberately a pure evaluator.  It reads release, source,
evaluator, qualification, and runtime-profile metadata supplied by a caller;
it does not read or mutate the catalogue, role-pack manifests, configuration,
deployments, or external systems.  The PKT-22 dependency remains an explicit
admission hold until exact role-pack manifests are present and independently
validated.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


PREPARATORY_STATUS = "PREPARATORY_ONLY"
PKT22_DEPENDENCY = {
    "packet": "PKT-22",
    "status": "unresolved",
    "required_for": "exact reusable role-pack manifests and role applicability",
    "effect": "no qualification admission or selectability claim",
}

_HEX64 = set("0123456789abcdef")
_DRAFT_STATES = {"draft", "eval_pending"}
_NONSELECTABLE_STATES = {
    "deprecated",
    "retired",
    "superseded",
    "withdrawn",
    "quarantined",
    "rejected",
    "incompatible",
    "unqualified",
}


class QualificationEvidenceError(ValueError):
    """Raised when an evidence input is not a deterministic mapping."""


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _digest(value: Any) -> str:
    """Return a stable digest for a JSON-compatible value."""

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _is_digest(value: Any) -> bool:
    text = _text(value)
    if text.startswith("sha256:"):
        text = text[7:]
    return len(text) == 64 and set(text) <= _HEX64


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise QualificationEvidenceError(f"{name}_must_be_object")
    return value


def _required_text(obj: Mapping[str, Any], field: str, reason: str, reasons: list[str]) -> str:
    value = _text(obj.get(field))
    if not value:
        reasons.append(reason)
    return value


def _identity_snapshot(release: Mapping[str, Any], reasons: list[str]) -> dict[str, Any]:
    provenance = release.get("provenance")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    release_id = _required_text(release, "release_id", "missing_release_identity", reasons)
    version = _required_text(release, "version", "missing_release_identity", reasons)
    bundle_hash = _text(release.get("bundle_hash") or release.get("artifact_digest"))
    if not _is_digest(bundle_hash):
        reasons.append("missing_release_identity")
    source_commit = _text(provenance.get("source_commit") or release.get("source_commit"))
    source_ref = _text(provenance.get("source_ref") or release.get("source_ref"))
    source_path = _text(provenance.get("source_path") or release.get("source_path"))
    repository = _text(provenance.get("repository"))
    source = {
        "repository": repository,
        "source_ref": source_ref,
        "source_commit": source_commit,
        "source_path": source_path,
    }
    if not all(source.values()) or len(source_commit) not in {40, 64}:
        reasons.append("missing_source_identity")
    return {
        "release_id": release_id,
        "version": version,
        "bundle_hash": bundle_hash,
        "source": source,
    }


def _evaluator_snapshot(evidence: Mapping[str, Any], reasons: list[str]) -> dict[str, Any]:
    evaluator = evidence.get("evaluator")
    if not isinstance(evaluator, Mapping):
        reasons.append("missing_evaluator_identity")
        return {"evaluator_id": "", "evaluator_version": "", "run_id": "", "result_digest": ""}
    snapshot = {
        "evaluator_id": _text(evaluator.get("evaluator_id")),
        "evaluator_version": _text(evaluator.get("evaluator_version")),
        "run_id": _text(evaluator.get("run_id")),
        "result_digest": _text(evaluator.get("result_digest")),
        "release_id": _text(evaluator.get("release_id")),
        "source_commit": _text(evaluator.get("source_commit")),
        "bundle_hash": _text(evaluator.get("bundle_hash")),
        "runtime_profile_id": _text(evaluator.get("runtime_profile_id")),
    }
    if not all(snapshot.values()) or not _is_digest(snapshot["result_digest"]) or not _is_digest(snapshot["bundle_hash"]):
        reasons.append("missing_evaluator_identity")
    return snapshot


def _qualification_snapshot(evidence: Mapping[str, Any], reasons: list[str]) -> dict[str, Any]:
    qualification = evidence.get("qualification")
    if not isinstance(qualification, Mapping):
        reasons.append("missing_qualification_metadata")
        return {"status": "missing", "evidence_ref": "", "result_digest": "", "release_id": "", "source_commit": "", "runtime_profile_id": ""}
    status = _text(qualification.get("status")).lower()
    evidence_ref = _text(qualification.get("evidence_ref"))
    result_digest = _text(qualification.get("result_digest"))
    snapshot = {
        "status": status or "missing",
        "evidence_ref": evidence_ref,
        "result_digest": result_digest,
        "release_id": _text(qualification.get("release_id")),
        "source_commit": _text(qualification.get("source_commit")),
        "runtime_profile_id": _text(qualification.get("runtime_profile_id")),
    }
    if not status or not evidence_ref or not _is_digest(result_digest) or not snapshot["release_id"] or not snapshot["source_commit"] or not snapshot["runtime_profile_id"]:
        reasons.append("missing_qualification_metadata")
    return snapshot


def _profile_snapshot(
    evidence: Mapping[str, Any],
    runtime_profile: Mapping[str, Any] | str | None,
    release: Mapping[str, Any],
    reasons: list[str],
) -> dict[str, Any]:
    profile = runtime_profile if isinstance(runtime_profile, Mapping) else {"profile_id": runtime_profile or ""}
    profile_id = _text(profile.get("profile_id") or profile.get("runtime_profile_id"))
    declared = release.get("compatible_runtime_profiles")
    if declared is None:
        declared = release.get("runtime_profiles")
    if isinstance(declared, str):
        declared_profiles = [declared] if declared else []
    elif isinstance(declared, Sequence) and not isinstance(declared, (bytes, bytearray)):
        declared_profiles = sorted({_text(item) for item in declared if _text(item)})
    else:
        declared_profiles = []
    evidence_profile = _text(evidence.get("runtime_profile_id"))
    if not profile_id or not evidence_profile:
        reasons.append("missing_runtime_profile_identity")
    if profile_id and evidence_profile and profile_id != evidence_profile:
        reasons.append("runtime_profile_identity_mismatch")
    if not declared_profiles or (profile_id and profile_id not in declared_profiles and "*" not in declared_profiles and "any" not in declared_profiles):
        reasons.append("incompatible_runtime_profile")
    return {"profile_id": profile_id, "declared_compatible_profiles": declared_profiles}


def _classification(reasons: Sequence[str], lifecycle: str, qualification_status: str) -> str:
    if any(reason.startswith("missing_") for reason in reasons):
        return "missing"
    if any(reason in {"evidence_release_id_mismatch", "evidence_bundle_hash_mismatch", "evidence_source_commit_mismatch", "evaluator_identity_mismatch", "qualification_identity_mismatch"} for reason in reasons):
        return "identity_mismatch"
    if lifecycle in _DRAFT_STATES:
        return "draft"
    if qualification_status != "certified":
        return "uncertified"
    if "incompatible_runtime_profile" in reasons or "runtime_profile_identity_mismatch" in reasons:
        return "incompatible"
    if lifecycle in _NONSELECTABLE_STATES:
        return lifecycle
    return "dependency_blocked"


def evaluate_release(
    release: Mapping[str, Any] | None,
    evidence: Mapping[str, Any] | None,
    runtime_profile: Mapping[str, Any] | str | None,
) -> dict[str, Any]:
    """Evaluate one release without ever admitting it as selectable.

    The result is a decision receipt, not a qualification result.  A release
    can only receive ``selectable: false`` from this preparatory harness.  All
    identity fields are copied from inputs, never generated as substitutes.
    """

    if release is None:
        release = {}
    if evidence is None:
        evidence = {}
    release = _mapping(release, "release")
    evidence = _mapping(evidence, "evidence")
    reasons: list[str] = []
    identity = _identity_snapshot(release, reasons)
    evaluator = _evaluator_snapshot(evidence, reasons)
    qualification = _qualification_snapshot(evidence, reasons)
    profile = _profile_snapshot(evidence, runtime_profile, release, reasons)

    # Every assertion must bind to the same immutable release/source.  A
    # matching-looking but independently supplied identity is not sufficient.
    for field, actual in (
        ("release_id", identity["release_id"]),
        ("bundle_hash", identity["bundle_hash"]),
        ("source_commit", identity["source"]["source_commit"]),
    ):
        if _text(evidence.get(field)) != actual:
            reasons.append(f"evidence_{field}_mismatch")
    evaluator = evidence.get("evaluator")
    if isinstance(evaluator, Mapping):
        if any(_text(evaluator.get(field)) != actual for field, actual in (("release_id", identity["release_id"]), ("bundle_hash", identity["bundle_hash"]), ("source_commit", identity["source"]["source_commit"]))):
            reasons.append("evaluator_identity_mismatch")
    qualification_metadata = evidence.get("qualification")
    if isinstance(qualification_metadata, Mapping):
        if any(_text(qualification_metadata.get(field)) != actual for field, actual in (("release_id", identity["release_id"]), ("source_commit", identity["source"]["source_commit"]))):
            reasons.append("qualification_identity_mismatch")
    if qualification.get("status") == "certified":
        if not _is_digest(qualification.get("result_digest")):
            reasons.append("uncertified_evidence_digest")

    reasons = sorted(set(reasons))
    classification = _classification(reasons, _text(release.get("lifecycle_state")).lower(), qualification["status"])
    if "incompatible_runtime_profile" in reasons and classification not in {"missing", "draft", "uncertified"}:
        classification = "incompatible"
    return {
        "schema_version": "0.1",
        "status": PREPARATORY_STATUS,
        "release": identity,
        "evaluator": evaluator,
        "qualification": qualification,
        "runtime_profile": profile,
        "classification": classification,
        "reason_codes": reasons,
        "selectable": False,
        "qualification_pass_claimed": False,
        "dependency": dict(PKT22_DEPENDENCY),
    }


def make_preparatory_receipt(decisions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build a stable aggregate receipt without retaining source/private data."""

    normalized = []
    for decision in decisions:
        item = _mapping(decision, "decision")
        normalized.append(
            {
                "release_id": _text(item.get("release", {}).get("release_id")) if isinstance(item.get("release"), Mapping) else "",
                "classification": _text(item.get("classification")),
                "selectable": False,
                "reason_codes": sorted({_text(reason) for reason in item.get("reason_codes", []) if _text(reason)}),
            }
        )
    normalized.sort(key=lambda item: (item["release_id"], item["classification"], item["reason_codes"]))
    receipt = {
        "schema_version": "0.1",
        "packet": "PKT-23",
        "status": PREPARATORY_STATUS,
        "dependency": dict(PKT22_DEPENDENCY),
        "qualification_pass_claimed": False,
        "selectable_release_count": 0,
        "decisions": normalized,
    }
    receipt["receipt_digest"] = _digest(receipt)
    return receipt
