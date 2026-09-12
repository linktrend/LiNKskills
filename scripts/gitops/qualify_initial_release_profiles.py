#!/usr/bin/env python3
"""Qualify the five frozen initial skill release/profile combinations.

This is a fail-closed, stdlib-only classifier. It never promotes a combination
to ``usable`` without executable eval-case evidence, never treats prompt-only
or fake-judge receipts as certification, and classifies each combination
independently so one missing artifact cannot rewrite an unrelated row.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = 1
MATRIX_KIND = "initial-release-profile-matrix"
USABLE = "usable"
EVAL_PENDING = "eval_pending"
QUARANTINED = "quarantined"
REQUIRED_FAMILIES = ("success", "guardrail", "failure", "recovery", "privacy")
FAKE_EVIDENCE_MARKERS = frozenset({"fake", "prompt_only", "prompt-only", "promptonly"})

INITIAL_RELEASE_PROFILES: tuple[dict[str, str], ...] = (
    {
        "skillId": "git-safeguard",
        "version": "1.1.0",
        "runtimeProfile": "cursor-macos",
    },
    {
        "skillId": "persistent-qa",
        "version": "1.0.0",
        "runtimeProfile": "cursor-macos",
    },
    {
        "skillId": "repository-manager",
        "version": "1.0.0",
        "runtimeProfile": "cursor-macos",
    },
    {
        "skillId": "skill-template",
        "version": "1.2.0",
        "runtimeProfile": "cursor-macos",
    },
    {
        "skillId": "tool-architect",
        "version": "1.0.0",
        "runtimeProfile": "cursor-macos",
    },
)

_FRONTMATTER_VERSION_RE = re.compile(r"(?m)^version:\s*[\"']?([0-9]+(?:\.[0-9]+){1,3})")
_YAML_CASE_ID_RE = re.compile(r"(?m)^\s*-\s+id:\s*[\"']?([A-Za-z0-9._-]+)")
_YAML_CASE_TYPE_RE = re.compile(r"(?m)^\s*case_type:\s*[\"']?([A-Za-z0-9._-]+)")
_SECRET_SCAN_ARGV = ["python3", "scripts/gitops/secret_scan.py"]


class QualificationError(ValueError):
    """A deterministic qualification-matrix failure."""


def digest_bytes(raw: bytes) -> str:
    """Return a sha256 digest with the canonical prefix."""
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def combination_id(skill_id: str, version: str, runtime_profile: str) -> str:
    """Return the stable identity for one release/profile pair."""
    return f"{skill_id}@{version}/{runtime_profile}"


def _frontmatter_version(skill_md: Path) -> str | None:
    if not skill_md.is_file():
        return None
    text = skill_md.read_text(encoding="utf-8")
    match = _FRONTMATTER_VERSION_RE.search(text)
    return match.group(1) if match else None


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QualificationError(f"artifact_unreadable:{path.as_posix()}:{exc}") from exc
    if not isinstance(data, dict):
        raise QualificationError(f"artifact_not_object:{path.as_posix()}")
    return data


def _case_records(skill_dir: Path) -> list[dict[str, Any]]:
    json_suite = skill_dir / "references" / "eval-suite.json"
    yaml_suite = skill_dir / "references" / "eval-suite.yaml"
    if json_suite.is_file():
        data = _load_json(json_suite) or {}
        raw_cases = data.get("cases") or data.get("scenarios") or []
        records: list[dict[str, Any]] = []
        if isinstance(raw_cases, list):
            for item in raw_cases:
                if not isinstance(item, dict):
                    continue
                case_id = str(item.get("case_id") or item.get("id") or "")
                if not case_id:
                    continue
                execute = item.get("execute")
                records.append(
                    {
                        "id": case_id,
                        "caseType": str(item.get("case_type") or ""),
                        "hasExecute": isinstance(execute, dict) and bool(execute),
                        "text": " ".join(
                            [
                                case_id,
                                str(item.get("case_type") or ""),
                                str(item.get("input") or ""),
                            ]
                        ).lower(),
                    }
                )
        return records
    if yaml_suite.is_file():
        text = yaml_suite.read_text(encoding="utf-8")
        ids = _YAML_CASE_ID_RE.findall(text)
        types = _YAML_CASE_TYPE_RE.findall(text)
        records = []
        lowered = text.lower()
        for index, case_id in enumerate(ids):
            case_type = types[index] if index < len(types) else ""
            records.append(
                {
                    "id": case_id,
                    "caseType": case_type,
                    "hasExecute": False,
                    "text": f"{case_id} {case_type} {lowered}",
                }
            )
        return records
    return []


def classify_case_families(cases: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    """Map suite cases onto the five required representative families."""
    families: dict[str, list[str]] = {name: [] for name in REQUIRED_FAMILIES}
    for case in cases:
        case_id = str(case.get("id") or "")
        if not case_id:
            continue
        blob = " ".join(
            [
                case_id,
                str(case.get("caseType") or ""),
                str(case.get("text") or ""),
            ]
        ).lower()
        case_type = str(case.get("caseType") or "").lower()
        if case_type == "golden" or any(
            token in blob for token in ("success", "allows", "clean", "scaffold", "create-new")
        ):
            families["success"].append(case_id)
        if case_type == "negative" or "guardrail" in blob or "refuse" in blob:
            families["guardrail"].append(case_id)
        if any(token in blob for token in ("fail", "block", "defect", "wrong-branch", "error")):
            families["failure"].append(case_id)
        if any(
            token in blob
            for token in ("recovery", "retry", "memory-failure", "unavailable", "outage")
        ):
            families["recovery"].append(case_id)
        if any(token in blob for token in ("secret", "privacy", "redact", "pii")):
            families["privacy"].append(case_id)
    for name, rows in families.items():
        families[name] = sorted(set(rows))
    return families


def _claimed_evidence_kind(row: Mapping[str, Any]) -> str:
    kind = str(row.get("evidenceKind") or row.get("judgeKind") or "").strip().lower()
    return kind.replace("-", "_")


def classify_combination(
    *,
    skill_id: str,
    version: str,
    runtime_profile: str,
    source_version: str | None,
    compatible_profiles: Sequence[str],
    families: Mapping[str, Sequence[str]],
    executable_case_ids: Sequence[str],
    evidence_kind: str = "",
    certified: bool = False,
) -> dict[str, Any]:
    """Classify one combination without consulting sibling rows."""
    combo = combination_id(skill_id, version, runtime_profile)
    missing_artifacts: list[str] = []
    if source_version is None:
        missing_artifacts.append("skill_frontmatter_version")
    elif source_version != version:
        missing_artifacts.append(f"version_mismatch:{source_version}")
    if runtime_profile not in set(compatible_profiles):
        missing_artifacts.append("runtime_profile_not_declared")
    missing_families = [name for name in REQUIRED_FAMILIES if not families.get(name)]
    executable = sorted({str(item) for item in executable_case_ids if item})
    kind = _claimed_evidence_kind({"evidenceKind": evidence_kind})
    reasons: list[str] = []
    if kind in FAKE_EVIDENCE_MARKERS:
        return {
            "id": combo,
            "skillId": skill_id,
            "version": version,
            "runtimeProfile": runtime_profile,
            "lifecycle": QUARANTINED,
            "missingFamilies": missing_families,
            "missingArtifacts": missing_artifacts,
            "executableCases": executable,
            "reason": "prompt_only_or_fake_evidence",
        }
    if certified and not executable:
        return {
            "id": combo,
            "skillId": skill_id,
            "version": version,
            "runtimeProfile": runtime_profile,
            "lifecycle": QUARANTINED,
            "missingFamilies": missing_families,
            "missingArtifacts": missing_artifacts,
            "executableCases": executable,
            "reason": "certified_without_executed_cases",
        }
    if (
        certified
        and not missing_families
        and not missing_artifacts
        and executable
        and kind not in FAKE_EVIDENCE_MARKERS
    ):
        lifecycle = USABLE
        reasons.append("executed_case_evidence")
    else:
        lifecycle = EVAL_PENDING
        if missing_families:
            reasons.append("missing_representative_families")
        if missing_artifacts:
            reasons.append("missing_or_mismatched_artifacts")
        if not executable:
            reasons.append("no_executed_cases")
        if not reasons:
            reasons.append("eval_pending")
    return {
        "id": combo,
        "skillId": skill_id,
        "version": version,
        "runtimeProfile": runtime_profile,
        "lifecycle": lifecycle,
        "missingFamilies": missing_families,
        "missingArtifacts": missing_artifacts,
        "executableCases": executable,
        "reason": ",".join(reasons),
    }


def qualify_skill(
    root: Path,
    declared: Mapping[str, str],
    *,
    evidence_kind: str = "",
    certified: bool = False,
) -> dict[str, Any]:
    """Load one frozen combination from source and classify it in isolation."""
    skill_id = declared["skillId"]
    version = declared["version"]
    runtime_profile = declared["runtimeProfile"]
    skill_dir = root / "skills" / skill_id
    pack = _load_json(skill_dir / "references" / "skill-pack.json") or {}
    profile = _load_json(skill_dir / "references" / "execution-profile.json") or {}
    source_version = _frontmatter_version(skill_dir / "SKILL.md")
    if source_version is None and pack.get("version"):
        source_version = str(pack["version"])
    compatible: list[str] = []
    raw_profiles = pack.get("compatible_runtime_profiles")
    if isinstance(raw_profiles, list):
        compatible.extend(str(item) for item in raw_profiles if item)
    runtime_id = profile.get("runtime_profile_id")
    if runtime_id and str(runtime_id) not in compatible:
        compatible.append(str(runtime_id))
    cases = _case_records(skill_dir)
    families = classify_case_families(cases)
    executable = [str(case["id"]) for case in cases if case.get("hasExecute")]
    row = classify_combination(
        skill_id=skill_id,
        version=version,
        runtime_profile=runtime_profile,
        source_version=source_version,
        compatible_profiles=compatible,
        families=families,
        executable_case_ids=executable,
        evidence_kind=evidence_kind,
        certified=certified,
    )
    row["families"] = families
    row["skillDir"] = str(skill_dir.relative_to(root).as_posix())
    if pack:
        row["skillPackDigest"] = digest_bytes(
            (skill_dir / "references" / "skill-pack.json").read_bytes()
        )
    return row


def qualify_initial_release_profiles(
    root: Path,
    *,
    declared: Sequence[Mapping[str, str]] | None = None,
    overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return the complete five-row matrix. Sibling rows never share failure."""
    combinations = list(declared or INITIAL_RELEASE_PROFILES)
    if len(combinations) != 5:
        raise QualificationError("initial_release_profile_count_invalid")
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for item in combinations:
        combo = combination_id(item["skillId"], item["version"], item["runtimeProfile"])
        if combo in seen:
            raise QualificationError(f"duplicate_combination:{combo}")
        seen.add(combo)
        extra = dict(overrides.get(combo, {}) if overrides else {})
        try:
            row = qualify_skill(
                root,
                item,
                evidence_kind=str(extra.get("evidenceKind") or ""),
                certified=bool(extra.get("certified")),
            )
        except QualificationError as exc:
            row = {
                "id": combo,
                "skillId": item["skillId"],
                "version": item["version"],
                "runtimeProfile": item["runtimeProfile"],
                "lifecycle": QUARANTINED,
                "missingFamilies": list(REQUIRED_FAMILIES),
                "missingArtifacts": [str(exc)],
                "executableCases": [],
                "reason": str(exc),
                "families": {name: [] for name in REQUIRED_FAMILIES},
            }
        rows.append(row)
    usable = [row["id"] for row in rows if row["lifecycle"] == USABLE]
    pending = [row["id"] for row in rows if row["lifecycle"] == EVAL_PENDING]
    quarantined = [row["id"] for row in rows if row["lifecycle"] == QUARANTINED]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": MATRIX_KIND,
        "complete": len(rows) == 5,
        "ok": len(rows) == 5 and not quarantined,
        "combinations": rows,
        "usable": usable,
        "evalPending": pending,
        "quarantined": quarantined,
    }


def delivery_secret_scan_preserved(root: Path) -> bool:
    """True when Fast and Full still invoke the fixture-aware secret scanner."""
    config = root / ".ide-development" / "config" / "delivery.json"
    payload = json.loads(config.read_text(encoding="utf-8"))
    profiles = payload.get("profiles") or {}
    for name in ("fast", "full"):
        commands = (profiles.get(name) or {}).get("commands") or []
        if _SECRET_SCAN_ARGV not in commands:
            return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--matrix-json", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = args.root.resolve()
    matrix = qualify_initial_release_profiles(root)
    matrix["secretScanPreserved"] = delivery_secret_scan_preserved(root)
    if not matrix["secretScanPreserved"]:
        matrix["ok"] = False
        matrix["secretScanReason"] = "fast_or_full_missing_secret_scan"
    text = json.dumps(matrix, indent=2, sort_keys=True) + "\n"
    if args.matrix_json:
        args.matrix_json.parent.mkdir(parents=True, exist_ok=True)
        args.matrix_json.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if matrix["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
