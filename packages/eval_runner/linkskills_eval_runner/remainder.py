"""Remainder qualification matrix.

The five production-successor releases stay owned by ``ed03``. This module
inventories every other catalog skill, requires executable confined cases, and
never mints ``usable`` from filesystem presence, source helper output, or
reused five-release evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from linkskills_core.hashing import stamp_execution_profile

from .consumer_profiles import (
    CURSOR_MACOS,
    inspect_issuer_receipt,
    inspect_isolator_receipt,
    inspect_sealed_image_receipt,
    resolve_driver,
)
from .ed03 import (
    EVAL_PENDING,
    INITIAL_RELEASE_PROFILES,
    QUARANTINED,
    SCHEMA_VERSION,
    USABLE,
    QualificationError,
    _compatible_profiles,
    _frontmatter_version,
    case_records,
    classify_case_families,
    classify_combination,
    combination_id,
    run_combination,
    source_digests,
)

REMAINDER_KIND = "remainder-release-profile-matrix"
HOSTED_REMAINDER_KIND = "hosted-remainder-release-profile-matrix"
INITIAL_SKILL_IDS = frozenset(item["skillId"] for item in INITIAL_RELEASE_PROFILES)
UNPUBLISHED_SKILL_IDS = frozenset({"private-health-wellbeing", "personal-compliance"})
REQUIRED_REMAINDER_COUNT = 80
SHARED_FLOOR_REMAINDER_COUNT = 78


def catalog_skill_ids(root: Path) -> list[str]:
    skills = root / "skills"
    return sorted(path.parent.name for path in skills.glob("*/SKILL.md") if path.is_file())


def remainder_skill_ids(root: Path) -> list[str]:
    return [skill_id for skill_id in catalog_skill_ids(root) if skill_id not in INITIAL_SKILL_IDS]


def shared_floor_remainder_skill_ids(root: Path) -> list[str]:
    """Remainder ids that may become live. The two private skills stay unpublished."""
    return [
        skill_id
        for skill_id in remainder_skill_ids(root)
        if skill_id not in UNPUBLISHED_SKILL_IDS
    ]


def declared_remainder_profiles(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for skill_id in remainder_skill_ids(root):
        skill_dir = root / "skills" / skill_id
        version = _frontmatter_version(skill_dir / "SKILL.md") or "0.0.0"
        rows.append(
            {
                "skillId": skill_id,
                "version": version,
                "runtimeProfile": CURSOR_MACOS,
            }
        )
    return rows


def qualify_remainder_release_profiles(
    root: Path,
    *,
    declared: Sequence[Mapping[str, str]] | None = None,
    evidence_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """Source-only remainder matrix. Never authorizes usable."""
    del evidence_dir
    combinations = list(declared or declared_remainder_profiles(root))
    expected = remainder_skill_ids(root)
    if {item["skillId"] for item in combinations} != set(expected):
        raise QualificationError("remainder_skill_set_mismatch")
    if len(combinations) != REQUIRED_REMAINDER_COUNT:
        raise QualificationError(f"remainder_count_invalid:{len(combinations)}")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in combinations:
        skill_id = str(item["skillId"])
        version = str(item["version"])
        runtime_profile = str(item["runtimeProfile"])
        combo = combination_id(skill_id, version, runtime_profile)
        if combo in seen:
            raise QualificationError(f"duplicate_combination:{combo}")
        seen.add(combo)
        skill_dir = root / "skills" / skill_id
        cases = case_records(skill_dir)
        families = classify_case_families(cases)
        executable = [c["id"] for c in cases if c.get("hasExecute")]
        driver = resolve_driver(runtime_profile)
        missing = list(driver.binding(root).get("missingOwnerReceipts") or [])
        compatible = _compatible_profiles(skill_dir) or [runtime_profile]
        row = classify_combination(
            skill_id=skill_id,
            version=version,
            runtime_profile=runtime_profile,
            source_version=_frontmatter_version(skill_dir / "SKILL.md"),
            compatible_profiles=compatible,
            families=families,
            executable_case_ids=executable,
            evidence_kind="source_validation_only",
            certified=False,
            missing_owner_receipts=missing,
            sealed_receipts=False,
        )
        if row["lifecycle"] == USABLE:
            row["lifecycle"] = EVAL_PENDING
            row["reason"] = "usable_forbidden_without_hosted_sealed_receipts"
        row["families"] = families
        row["skillDir"] = str(skill_dir.relative_to(root).as_posix())
        row["digests"] = source_digests(skill_dir)
        row["evidenceClass"] = "source_executable_not_production"
        rows.append(row)
    pending = [row["id"] for row in rows if row["lifecycle"] == EVAL_PENDING]
    quarantined = [row["id"] for row in rows if row["lifecycle"] == QUARANTINED]
    missing_execute = [row["id"] for row in rows if not row.get("executableCases")]
    missing_families = [row["id"] for row in rows if row.get("missingFamilies")]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": REMAINDER_KIND,
        "complete": len(rows) == REQUIRED_REMAINDER_COUNT,
        "ok": len(rows) == REQUIRED_REMAINDER_COUNT
        and not missing_execute
        and not missing_families
        and not quarantined,
        "usableClaimed": False,
        "authorizesUsable": False,
        "initialProductionSuccessor": [
            combination_id(i["skillId"], i["version"], i["runtimeProfile"])
            for i in INITIAL_RELEASE_PROFILES
        ],
        "remainderCount": len(rows),
        "combinations": rows,
        "usable": [],
        "evalPending": pending,
        "quarantined": quarantined,
        "missingExecutable": missing_execute,
        "missingFamilies": missing_families,
        "issuerReceipt": inspect_issuer_receipt(),
        "sealedImageReceipt": inspect_sealed_image_receipt(),
        "isolatorReceipt": inspect_isolator_receipt(),
        "liveQualificationBoundary": "server01_hosted_sealed_evaluator",
    }


def qualify_hosted_remainder_release_profiles(
    root: Path,
    *,
    evidence_dir: Optional[Path] = None,
    only_skill_ids: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    """Run confined suites for shared-floor remainder ids.

    Source ``qualify_remainder_release_profiles`` stays uncertified. Usable
    rows come only from executed bubblewrap receipts with isolation denied.
    ``only_skill_ids`` limits execution to that shared-floor subset. The two
    private skills stay unpublished.
    """
    source = qualify_remainder_release_profiles(root)
    if source.get("usable") or source.get("usableClaimed") or source.get("authorizesUsable"):
        raise QualificationError("source_remainder_matrix_claimed_usable")
    shared = shared_floor_remainder_skill_ids(root)
    if only_skill_ids is None:
        selected = list(shared)
    else:
        selected = [str(item) for item in only_skill_ids]
        if not selected or len(selected) != len(set(selected)):
            raise QualificationError("remainder_only_skill_ids_invalid")
        blocked = [item for item in selected if item in UNPUBLISHED_SKILL_IDS]
        if blocked:
            raise QualificationError("unpublished_skill_forbidden:" + ",".join(blocked))
        unknown = [item for item in selected if item not in set(shared)]
        if unknown:
            raise QualificationError("remainder_skill_not_shared_floor:" + ",".join(unknown))
    declared = [
        item
        for item in declared_remainder_profiles(root)
        if item["skillId"] in set(selected)
    ]
    if len(declared) != len(selected):
        raise QualificationError(f"shared_floor_remainder_count_invalid:{len(declared)}")
    rows: list[dict[str, Any]] = []
    for item in declared:
        try:
            row = run_combination(root, item, evidence_dir=evidence_dir)
        except RuntimeError as exc:
            if "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY" not in str(exc):
                raise
            skill_dir = root / "skills" / item["skillId"]
            cases = case_records(skill_dir)
            families = classify_case_families(cases)
            row = classify_combination(
                skill_id=item["skillId"],
                version=item["version"],
                runtime_profile=item["runtimeProfile"],
                source_version=_frontmatter_version(skill_dir / "SKILL.md"),
                compatible_profiles=_compatible_profiles(skill_dir) or [item["runtimeProfile"]],
                families=families,
                executable_case_ids=[c["id"] for c in cases if c.get("hasExecute")],
                evidence_kind="independent_deterministic",
                certified=False,
                sealed_receipts=False,
            )
            row["families"] = families
            row["skillDir"] = str(skill_dir.relative_to(root).as_posix())
            row["digests"] = source_digests(skill_dir)
            row["run"] = {
                "passed": False,
                "certified": False,
                "certifyReason": "issuer_material_missing",
                "receiptHashes": [],
                "networkIsolation": [],
            }
        if row["skillId"] in UNPUBLISHED_SKILL_IDS:
            raise QualificationError(f"unpublished_skill_executed:{row['skillId']}")
        rows.append(row)
    usable = [row["id"] for row in rows if row["lifecycle"] == USABLE]
    pending = [row["id"] for row in rows if row["lifecycle"] == EVAL_PENDING]
    quarantined = [row["id"] for row in rows if row["lifecycle"] == QUARANTINED]
    sealed = [
        row["id"]
        for row in rows
        if row["lifecycle"] == USABLE
        and bool((row.get("run") or {}).get("certified"))
        and bool((row.get("run") or {}).get("receiptHashes"))
        and all(item == "denied" for item in (row.get("run") or {}).get("networkIsolation") or [])
    ]
    if set(usable) != set(sealed):
        usable = [combo for combo in usable if combo in sealed]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": HOSTED_REMAINDER_KIND,
        "complete": len(rows) == len(selected),
        "ok": len(rows) == len(selected) and not quarantined,
        "onlySkillIds": selected if only_skill_ids is not None else [],
        "usableClaimed": bool(usable),
        "authorizesUsable": bool(usable),
        "sourceMatrixAuthorizesUsable": False,
        "unpublished": sorted(UNPUBLISHED_SKILL_IDS),
        "remainderCount": source["remainderCount"],
        "sharedFloorCount": len(rows),
        "combinations": rows,
        "usable": usable,
        "evalPending": pending,
        "quarantined": quarantined,
        "issuerReceipt": inspect_issuer_receipt(),
        "sealedImageReceipt": inspect_sealed_image_receipt(),
        "isolatorReceipt": inspect_isolator_receipt(),
        "liveQualificationBoundary": "server01_hosted_sealed_evaluator",
    }


def stamp_remainder_execution_profiles(root: Path) -> dict[str, str]:
    written: dict[str, str] = {}
    for item in declared_remainder_profiles(root):
        skill_dir = root / "skills" / item["skillId"]
        profile_path = skill_dir / "references" / "execution-profile.json"
        if not profile_path.is_file():
            continue
        if not (skill_dir / "references" / "eval-suite.json").is_file():
            continue
        profile = stamp_execution_profile(
            skill_dir,
            runtime_profile_id=item["runtimeProfile"],
            lifecycle_state="draft",
        )
        profile_path.write_text(
            json.dumps(profile, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written[item["skillId"]] = str(profile["profile_hash"])
    return written
