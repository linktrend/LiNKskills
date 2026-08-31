"""Exact PKT-22 source metadata for role-pack release references.

This module reads repository-owned skill trees and emits draft, inactive
release and eligibility records.  It does not qualify releases, invent
runtime profiles, activate consumers, or claim hosted/VPS/production proof.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_PACKAGES_CORE = _ROOT / "packages" / "core"
for _path in (Path(__file__).resolve().parent, _PACKAGES_CORE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from linkskills_core.hashing import build_skill_bundle_manifest  # noqa: E402

from role_pack_validator import load_role_pack_inputs  # noqa: E402

PROTECTED_BASE = {
    "ref": "origin/development",
    "commit": "1289f9a374c38115d3f4dcfac31439a9904d74c6",
    "tree": "8d3312b21ccfa92102233211f8224d50fb07ac88",
}
EVALUATED_AT = "2026-08-31T00:00:00Z"
ROLE_PACK_DIR = _ROOT / "role-packs"
RELEASE_DIR = ROLE_PACK_DIR / "releases"
ELIGIBILITY_DIR = ROLE_PACK_DIR / "eligibility"
MANIFEST_STEMS = (
    "lisa-ceo",
    "eric-cto",
    "david-cpo",
    "sara-coo-cfo",
    "jane-chief-trading-officer",
)
FALSE_CLAIMS = {
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
}


def _read_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"expected object: {path}")
    return value


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def iter_manifest_paths() -> tuple[Path, ...]:
    """Return the five PKT-22 role-pack manifest paths in stable order."""

    return tuple(ROLE_PACK_DIR / f"{stem}.json" for stem in MANIFEST_STEMS)


def referenced_release_ids() -> tuple[str, ...]:
    """Return unique release identities referenced by the five manifests."""

    ids: list[str] = []
    seen: set[str] = set()
    for path in iter_manifest_paths():
        payload = _read_json(path)
        for entry in payload.get("release_refs") or []:
            if not isinstance(entry, Mapping):
                continue
            release_id = entry.get("release_id")
            if isinstance(release_id, str) and release_id and release_id not in seen:
                seen.add(release_id)
                ids.append(release_id)
    return tuple(ids)


def skill_id_from_release_id(release_id: str) -> str:
    """Split ``skill@version`` without substituting a missing skill."""

    skill_id, separator, _version = release_id.partition("@")
    if not separator or not skill_id:
        raise ValueError(f"malformed release_id: {release_id}")
    return skill_id


def eligibility_id_for(release_id: str) -> str:
    """Return the opaque eligibility identity bound to one exact release."""

    return f"{skill_id_from_release_id(release_id)}-1"


def build_release_record(release_id: str) -> dict[str, Any]:
    """Build a draft native release record from the exact skill tree."""

    skill_id = skill_id_from_release_id(release_id)
    skill_dir = _ROOT / "skills" / skill_id
    if not skill_dir.is_dir():
        raise FileNotFoundError(f"missing exact skill tree for {release_id}: {skill_dir}")
    bundle = build_skill_bundle_manifest(skill_dir)
    if bundle["version"] != release_id.split("@", 1)[1]:
        raise ValueError(f"skill version does not equal release_id version: {release_id}")
    pack_path = skill_dir / "references" / "skill-pack.json"
    pack = _read_json(pack_path) if pack_path.is_file() else {}
    lifecycle = pack.get("lifecycle_state") if isinstance(pack.get("lifecycle_state"), str) else "draft"
    declared_profiles = pack.get("compatible_runtime_profiles")
    execution_profiles = list(declared_profiles) if isinstance(declared_profiles, list) else []
    eligibility_ref = f"opaque:eligibility:{eligibility_id_for(release_id)}"
    source_path = f"skills/{skill_id}"
    return {
        "schema_version": "0.1",
        "release_id": release_id,
        "artifact_kind": "skill_pack",
        "artifact_id": skill_id,
        "version": bundle["version"],
        "bundle_hash": bundle["bundle_hash"],
        "channel": "development",
        "lifecycle_state": lifecycle,
        "published_at": EVALUATED_AT,
        "publisher": "LiNKskills",
        "source_commit": PROTECTED_BASE["commit"],
        "source_ref": PROTECTED_BASE["ref"],
        "source_path": source_path,
        "execution_profiles": execution_profiles,
        "eligibility_ref": eligibility_ref,
        "release_kind": "native",
        "inventory_digest": bundle["content_hash"],
        "content_digest": bundle["content_hash"],
        "retrieved_at": EVALUATED_AT,
        "notes": "PKT-22 exact source identity only; draft/unqualified and not selectable.",
        "provenance": {
            "publisher": "LiNKskills",
            "repository": "https://github.com/linktrend/LiNKskills",
            "source_ref": PROTECTED_BASE["ref"],
            "source_commit": PROTECTED_BASE["commit"],
            "source_path": source_path,
            "retrieved_at": EVALUATED_AT,
            "licence": "LiNKtrend internal",
            "trust_boundary": "linkskills-release-provenance",
        },
        "lineage": {
            "kind": "native",
            "upstream_release_id": None,
            "relationship": "none",
        },
        "resource_descriptors": [f"opaque:resource:{skill_id}-skill-md"],
        "attestation": {
            "algorithm": "ES256",
            "key_id": "linkskills-draft-unqualified",
            "issuer": "linkskills-publisher",
            "claims_digest": bundle["bundle_hash"],
            "signature": "draft-unqualified-no-signature",
            "trust_boundary": "linkskills-release-attestation",
        },
        "manifest": {
            "file_count": bundle["file_count"],
            "total_bytes": sum(int(entry["size"]) for entry in bundle["entry_hashes"]),
            "entry_hashes": bundle["entry_hashes"],
        },
    }


def build_eligibility_record(release_id: str) -> dict[str, Any]:
    """Build an ineligible four-gate record for one exact release."""

    eligibility_id = eligibility_id_for(release_id)
    evidence_ref = f"opaque:evidence:{skill_id_from_release_id(release_id)}-pkt-22-unqualified"

    def gate() -> dict[str, Any]:
        return {
            "status": False,
            "evidence_ref": evidence_ref,
            "evaluated_by": "linkskills-pkt-22-source",
        }

    return {
        "schema_version": "0.1",
        "eligibility_id": eligibility_id,
        "release_id": release_id,
        "evaluated_at": EVALUATED_AT,
        "platform_technical_eligibility": gate(),
        "skills_release_selectability": gate(),
        "consumer_profile_activation": gate(),
        "consumer_tool_authority": gate(),
        "decision": "ineligible",
        "denial_reasons": [
            "missing_platform_evidence",
            "release_not_selectable",
            "profile_not_activated",
            "tool_not_authorized",
            "unqualified",
        ],
        "trust_boundary": "linkskills-eligibility",
    }


def rebind_manifest(path: Path, releases_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Copy a role pack and bind each reference to the exact computed digest."""

    payload = dict(_read_json(path))
    rebound: list[dict[str, Any]] = []
    for entry in payload.get("release_refs") or []:
        if not isinstance(entry, Mapping):
            raise ValueError(f"malformed release_refs in {path}")
        release_id = entry.get("release_id")
        if not isinstance(release_id, str) or release_id not in releases_by_id:
            raise ValueError(f"missing exact release record for {release_id}")
        release = releases_by_id[release_id]
        rebound.append(
            {
                "release_id": release_id,
                "artifact_digest": release["bundle_hash"],
                "eligibility_ref": release["eligibility_ref"],
                "required": bool(entry.get("required", True)),
            }
        )
    payload["release_refs"] = rebound
    return payload


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write canonical pretty JSON for reviewable source evidence."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize_source_metadata() -> dict[str, Any]:
    """Write exact release/eligibility records, rebound manifests, and a HOLD receipt."""

    releases = {release_id: build_release_record(release_id) for release_id in referenced_release_ids()}
    for stale in list(RELEASE_DIR.glob("*.json")) if RELEASE_DIR.is_dir() else []:
        stale.unlink()
    for stale in list(ELIGIBILITY_DIR.glob("*.json")) if ELIGIBILITY_DIR.is_dir() else []:
        stale.unlink()
    for release_id, record in releases.items():
        write_json(RELEASE_DIR / f"{skill_id_from_release_id(release_id)}.json", record)
        write_json(ELIGIBILITY_DIR / f"{eligibility_id_for(release_id)}.json", build_eligibility_record(release_id))
    for path in iter_manifest_paths():
        write_json(path, rebind_manifest(path, releases))
    receipt = make_source_receipt()
    write_json(ROLE_PACK_DIR / "pkt-22-source-receipt.json", receipt)
    write_json(
        ROLE_PACK_DIR / "qualification-closure.json",
        make_qualification_closure(receipt, referenced_release_ids()),
    )
    return receipt


def validate_all_role_packs() -> list[dict[str, Any]]:
    """Validate every PKT-22 manifest against committed exact metadata."""

    results: list[dict[str, Any]] = []
    for path in iter_manifest_paths():
        results.append(
            load_role_pack_inputs(
                path,
                RELEASE_DIR,
                ELIGIBILITY_DIR,
                ROLE_PACK_DIR / "qualifications",
            )
        )
    return results


def make_source_receipt() -> dict[str, Any]:
    """Aggregate fail-closed PKT-22 source validation without a pass claim."""

    results = validate_all_role_packs()
    violation_codes = sorted({item["code"] for result in results for item in result["violations"]})
    named_holds = []
    if any(result["violations"] for result in results):
        named_holds.extend(
            [
                "qualification_evidence_missing",
                "lifecycle_state_is_not_qualification_evidence",
                "skills_release_selectability_is_an_independent_gate",
            ]
        )
    if "incompatible_runtime_profile" in violation_codes:
        named_holds.append("undeclared_or_non_intersecting_runtime_profiles")
    receipt = {
        "schema_version": "0.1",
        "packet": "PKT-22",
        "status": "HOLD",
        "admitted": False,
        "proof_scope": "source",
        "protected_base": dict(PROTECTED_BASE),
        "role_pack_count": len(results),
        "release_reference_count": sum(result["release_reference_count"] for result in results),
        "unique_release_count": len(referenced_release_ids()),
        "admitted_role_pack_ids": [result["role_pack_id"] for result in results if result["admitted"]],
        "hold_role_pack_ids": [result["role_pack_id"] for result in results if not result["admitted"]],
        "violation_codes": violation_codes,
        "named_holds": named_holds,
        "qualification_directory": "role-packs/qualifications",
        "qualification_records_present": False,
        "claims": dict(FALSE_CLAIMS),
        "role_packs": [
            {
                "role_pack_id": result["role_pack_id"],
                "status": result["status"],
                "admitted": result["admitted"],
                "release_reference_count": result["release_reference_count"],
                "violation_codes": sorted({item["code"] for item in result["violations"]}),
            }
            for result in results
        ],
    }
    receipt["receipt_digest"] = _canonical_digest(receipt)
    return receipt


def make_qualification_closure(receipt: Mapping[str, Any], release_ids: tuple[str, ...]) -> dict[str, Any]:
    """Record that PKT-22 closed selectability truthfully as HOLD."""

    return {
        "schema_version": "0.1",
        "kind": "role-pack-qualified-release-closure",
        "packet": "PKT-22",
        "state": "HOLD",
        "qualification_evidence_policy": (
            "independent qualification evidence is required and is not inferred from "
            "lifecycle_state, opaque eligibility receipts, or manifest presence; "
            "no live pointer or activation is created"
        ),
        "runtime_profiles": ["cursor-macos", "codex-macos"],
        "release_ids": list(release_ids),
        "protected_base": dict(PROTECTED_BASE),
        "receipt_digest": receipt["receipt_digest"],
        "claims": dict(FALSE_CLAIMS),
    }


def main(argv: list[str] | None = None) -> int:
    """Materialize or check PKT-22 exact source metadata."""

    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] not in {"--write", "--check"}:
        print("usage: python3 role-packs/source_metadata.py [--write|--check]", file=sys.stderr)
        return 2
    write = not args or args[0] == "--write"
    if write:
        receipt = materialize_source_metadata()
    else:
        receipt = make_source_receipt()
        committed = _read_json(ROLE_PACK_DIR / "pkt-22-source-receipt.json")
        if committed != receipt:
            print("pkt-22-source-receipt.json does not match live validation", file=sys.stderr)
            return 1
    print(json.dumps({"status": receipt["status"], "admitted": receipt["admitted"], "receipt_digest": receipt["receipt_digest"]}, indent=2))
    return 0 if receipt["status"] == "HOLD" and receipt["admitted"] is False else 1


if __name__ == "__main__":
    raise SystemExit(main())
