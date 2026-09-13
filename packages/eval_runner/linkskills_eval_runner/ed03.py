"""ED-03 qualifier for the five initial release/profile combinations.

Fail-closed: prompt-only, fixture, source-only, or fake evidence cannot
produce ``usable``. Missing live owner receipts keep ``eval_pending``.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from linkskills_core.hashing import (
    eval_suite_file_hash,
    sha256_hex_file,
    sha256_prefixed,
    skill_release_hash,
    stamp_execution_profile,
    verify_execution_profile_hashes,
)
from linkskills_eval_runner.certify import certify_run
from linkskills_eval_runner.consumer_profiles import (
    CURSOR_MACOS,
    ConsumerProfileDriver,
    inspect_issuer_receipt,
    inspect_isolator_receipt,
    inspect_owner_receipt,
    inspect_sealed_image_receipt,
    resolve_driver,
)
from linkskills_eval_runner.executor import compute_skill_release_hash
from linkskills_eval_runner.judge import IndependentDeterministicJudge
from linkskills_eval_runner.runner import load_eval_suite, run_suite
from linkskills_eval_runner.workspace import EvalWorkspace

SCHEMA_VERSION = 1
MATRIX_KIND = "initial-release-profile-matrix"
USABLE = "usable"
EVAL_PENDING = "eval_pending"
QUARANTINED = "quarantined"
REQUIRED_FAMILIES = ("success", "guardrail", "failure", "recovery", "privacy")
FAKE_EVIDENCE_MARKERS = frozenset({"fake", "prompt_only", "prompt-only", "promptonly"})
_YAML_CASE_ID_RE = re.compile(r"(?m)^\s*-\s+id:\s*[\"']?([A-Za-z0-9._-]+)")
_FRONTMATTER_VERSION_RE = re.compile(r"(?m)^version:\s*[\"']?([0-9]+(?:\.[0-9]+){1,3})")

INITIAL_RELEASE_PROFILES: tuple[dict[str, str], ...] = (
    {"skillId": "git-safeguard", "version": "1.1.0", "runtimeProfile": CURSOR_MACOS},
    {"skillId": "persistent-qa", "version": "1.0.0", "runtimeProfile": CURSOR_MACOS},
    {"skillId": "repository-manager", "version": "1.0.0", "runtimeProfile": CURSOR_MACOS},
    {"skillId": "skill-template", "version": "1.2.0", "runtimeProfile": CURSOR_MACOS},
    {"skillId": "tool-architect", "version": "1.0.0", "runtimeProfile": CURSOR_MACOS},
)


class QualificationError(ValueError):
    """Deterministic qualification failure."""


def combination_id(skill_id: str, version: str, runtime_profile: str) -> str:
    return f"{skill_id}@{version}/{runtime_profile}"


def digest_bytes(raw: bytes) -> str:
    return sha256_prefixed(hashlib.sha256(raw).hexdigest())


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise QualificationError(f"artifact_not_object:{path.as_posix()}")
    return data


def _frontmatter_version(skill_md: Path) -> str | None:
    if not skill_md.is_file():
        return None
    match = _FRONTMATTER_VERSION_RE.search(skill_md.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def _yaml_has_execute(text: str, case_id: str) -> bool:
    marker = f"- id: {case_id}"
    idx = text.find(marker)
    if idx < 0:
        marker = f'- id: "{case_id}"'
        idx = text.find(marker)
    if idx < 0:
        return False
    nxt = text.find("\n  - id:", idx + 1)
    block = text[idx : nxt if nxt > 0 else None]
    return "kind: consumer_profile" in block or "kind: skill_script" in block or "kind: command" in block


def case_records(skill_dir: Path) -> list[dict[str, Any]]:
    """Prefer the executable YAML suite; JSON is schema-canonical but cannot hold execute."""
    yaml_suite = skill_dir / "references" / "eval-suite.yaml"
    json_suite = skill_dir / "references" / "eval-suite.json"
    records: list[dict[str, Any]] = []
    yaml_text = yaml_suite.read_text(encoding="utf-8") if yaml_suite.is_file() else ""
    if json_suite.is_file():
        data = _load_json(json_suite) or {}
        raw_cases = data.get("cases") or data.get("scenarios") or []
        if isinstance(raw_cases, list):
            for item in raw_cases:
                if not isinstance(item, dict):
                    continue
                case_id = str(item.get("case_id") or item.get("id") or "")
                if not case_id:
                    continue
                execute = item.get("execute")
                has_execute = (isinstance(execute, dict) and bool(execute.get("kind"))) or _yaml_has_execute(
                    yaml_text, case_id
                )
                records.append(
                    {
                        "id": case_id,
                        "caseType": str(item.get("case_type") or ""),
                        "hasExecute": has_execute,
                        "text": " ".join(
                            [case_id, str(item.get("case_type") or ""), str(item.get("input") or "")]
                        ).lower(),
                    }
                )
    if records:
        # YAML may add recovery/privacy cases not yet mirrored, or execute-only ids.
        for case_id in _YAML_CASE_ID_RE.findall(yaml_text):
            if any(row["id"] == case_id for row in records):
                if _yaml_has_execute(yaml_text, case_id):
                    for row in records:
                        if row["id"] == case_id:
                            row["hasExecute"] = True
                continue
            records.append(
                {
                    "id": case_id,
                    "caseType": "",
                    "hasExecute": _yaml_has_execute(yaml_text, case_id),
                    "text": case_id.lower(),
                }
            )
        return records
    if yaml_text:
        for case_id in _YAML_CASE_ID_RE.findall(yaml_text):
            records.append(
                {
                    "id": case_id,
                    "caseType": "",
                    "hasExecute": _yaml_has_execute(yaml_text, case_id),
                    "text": case_id.lower(),
                }
            )
    return records


def classify_case_families(cases: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    families: dict[str, list[str]] = {name: [] for name in REQUIRED_FAMILIES}
    for case in cases:
        case_id = str(case.get("id") or "")
        if not case_id:
            continue
        blob = " ".join(
            [case_id, str(case.get("caseType") or ""), str(case.get("text") or "")]
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


def _claimed_evidence_kind(kind: str) -> str:
    return str(kind or "").strip().lower().replace("-", "_")


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
    missing_owner_receipts: Sequence[Mapping[str, Any]] | None = None,
    sealed_receipts: bool = False,
) -> dict[str, Any]:
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
    kind = _claimed_evidence_kind(evidence_kind)
    missing_owners = [dict(row) for row in (missing_owner_receipts or [])]
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
            "missingOwnerReceipts": missing_owners,
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
            "missingOwnerReceipts": missing_owners,
            "reason": "certified_without_executed_cases",
        }
    if (
        certified
        and sealed_receipts
        and not missing_families
        and not missing_artifacts
        and executable
        and not missing_owners
        and kind not in FAKE_EVIDENCE_MARKERS
    ):
        lifecycle = USABLE
        reason = "executed_case_evidence"
    else:
        lifecycle = EVAL_PENDING
        reasons: list[str] = []
        if missing_families:
            reasons.append("missing_representative_families")
        if missing_artifacts:
            reasons.append("missing_or_mismatched_artifacts")
        if not executable:
            reasons.append("no_executed_cases")
        if missing_owners:
            reasons.append("missing_owner_receipt")
        if not sealed_receipts:
            reasons.append("sealed_receipts_unavailable")
        if not certified:
            reasons.append("not_certified")
        reason = ",".join(reasons) if reasons else "eval_pending"
    return {
        "id": combo,
        "skillId": skill_id,
        "version": version,
        "runtimeProfile": runtime_profile,
        "lifecycle": lifecycle,
        "missingFamilies": missing_families,
        "missingArtifacts": missing_artifacts,
        "executableCases": executable,
        "missingOwnerReceipts": missing_owners,
        "reason": reason,
    }


def _compatible_profiles(skill_dir: Path) -> list[str]:
    pack = _load_json(skill_dir / "references" / "skill-pack.json") or {}
    profile = _load_json(skill_dir / "references" / "execution-profile.json") or {}
    compatible: list[str] = []
    raw_profiles = pack.get("compatible_runtime_profiles")
    if isinstance(raw_profiles, list):
        compatible.extend(str(item) for item in raw_profiles if item)
    runtime_id = profile.get("runtime_profile_id")
    if runtime_id and str(runtime_id) not in compatible:
        compatible.append(str(runtime_id))
    return compatible


def source_digests(skill_dir: Path) -> dict[str, Any]:
    yaml_suite = skill_dir / "references" / "eval-suite.yaml"
    json_suite = skill_dir / "references" / "eval-suite.json"
    helper = skill_dir / "scripts" / "helper_tool.py"
    profile = skill_dir / "references" / "execution-profile.json"
    pack = skill_dir / "references" / "skill-pack.json"
    return {
        "skillReleaseHash": skill_release_hash(skill_dir),
        "evalSuiteFileHash": eval_suite_file_hash(skill_dir),
        "evalSuiteYamlDigest": (
            sha256_prefixed(sha256_hex_file(yaml_suite)) if yaml_suite.is_file() else None
        ),
        "evalSuiteJsonDigest": (
            sha256_prefixed(sha256_hex_file(json_suite)) if json_suite.is_file() else None
        ),
        "toolScriptDigest": sha256_prefixed(sha256_hex_file(helper)) if helper.is_file() else None,
        "executionProfileDigest": (
            sha256_prefixed(sha256_hex_file(profile)) if profile.is_file() else None
        ),
        "skillPackDigest": sha256_prefixed(sha256_hex_file(pack)) if pack.is_file() else None,
        "profileHashErrors": verify_execution_profile_hashes(skill_dir),
    }


def run_combination(
    root: Path,
    declared: Mapping[str, str],
    *,
    evidence_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """Execute the YAML suite through the confined consumer-profile driver."""
    skill_id = declared["skillId"]
    version = declared["version"]
    runtime_profile = declared["runtimeProfile"]
    skill_dir = root / "skills" / skill_id
    suite_path = skill_dir / "references" / "eval-suite.yaml"
    driver: ConsumerProfileDriver = resolve_driver(runtime_profile)
    toolchain = driver.toolchain(root)
    binding = toolchain["consumer_profile_driver"]
    cases = case_records(skill_dir)
    families = classify_case_families(cases)
    executable = [str(case["id"]) for case in cases if case.get("hasExecute")]
    source_version = _frontmatter_version(skill_dir / "SKILL.md")
    pack = _load_json(skill_dir / "references" / "skill-pack.json") or {}
    if source_version is None and pack.get("version"):
        source_version = str(pack["version"])
    digests = source_digests(skill_dir)
    missing_owners = list(binding.get("missingOwnerReceipts") or [])

    run_payload: dict[str, Any] = {
        "suitePath": str(suite_path.relative_to(root).as_posix()) if suite_path.is_file() else None,
        "passed": False,
        "certified": False,
        "certifyReason": "suite_missing",
        "judgeKind": None,
        "receiptHashes": [],
        "networkIsolation": [],
        "cases": [],
        "skillReleaseHash": None,
        "executionProfileHash": None,
        "suiteHash": None,
    }

    if suite_path.is_file():
        suite = load_eval_suite(suite_path)
        release_hash = compute_skill_release_hash(skill_dir)
        workspace = EvalWorkspace()
        try:
            result = run_suite(
                suite,
                judge=IndependentDeterministicJudge(),
                toolchain=toolchain,
                workspace=workspace,
                repo_root=root,
                skill_dir=skill_dir,
                skill_release_hash=release_hash,
            )
            decision = certify_run(
                result,
                judge=IndependentDeterministicJudge(),
                rubric=suite.rubric,
                pass_threshold=suite.pass_threshold,
                expected_skill_release_hash=release_hash,
            )
            isolations = [
                str((c.execution_receipt or {}).get("network_isolation") or "")
                for c in result.case_results
            ]
            run_payload = {
                "suitePath": str(suite_path.relative_to(root).as_posix()),
                "passed": bool(result.passed),
                "certified": bool(decision.certified),
                "certifyReason": decision.reason,
                "judgeKind": result.judge_kind,
                "receiptHashes": list(decision.receipt_hashes),
                "networkIsolation": isolations,
                "weightedScore": decision.weighted_score,
                "cases": [
                    {
                        "caseId": c.case_id,
                        "status": c.status.value,
                        "reason": c.reason,
                        "evidenceSource": c.evidence_source,
                        "receiptHash": (c.execution_receipt or {}).get("receipt_hash"),
                        "adapterKind": (
                            ((c.execution_receipt or {}).get("tool_calls") or [{}])[0].get(
                                "adapter_kind"
                            )
                        ),
                        "networkIsolation": (c.execution_receipt or {}).get("network_isolation"),
                    }
                    for c in result.case_results
                ],
                "skillReleaseHash": decision.skill_release_hash or release_hash,
                "executionProfileHash": decision.profile_hash,
                "suiteHash": result.suite_hash,
                "reasons": list(result.reasons),
            }
            if evidence_dir is not None:
                combo = combination_id(skill_id, version, runtime_profile)
                target = evidence_dir / combo.replace("/", "__")
                target.mkdir(parents=True, exist_ok=True)
                (target / "run.json").write_text(
                    json.dumps(run_payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                for case in result.case_results:
                    if case.execution_receipt:
                        name = f"{case.case_id}.receipt.json"
                        (target / name).write_text(
                            json.dumps(case.execution_receipt, indent=2, sort_keys=True)
                            + "\n",
                            encoding="utf-8",
                        )
        finally:
            workspace.cleanup()

    sealed = bool(
        run_payload.get("certified")
        and run_payload.get("receiptHashes")
        and run_payload.get("networkIsolation")
        and all(item == "denied" for item in run_payload["networkIsolation"])
        and not missing_owners
    )
    row = classify_combination(
        skill_id=skill_id,
        version=version,
        runtime_profile=runtime_profile,
        source_version=source_version,
        compatible_profiles=_compatible_profiles(skill_dir),
        families=families,
        executable_case_ids=executable,
        evidence_kind=str(run_payload.get("judgeKind") or "independent_deterministic"),
        certified=bool(run_payload.get("certified")),
        missing_owner_receipts=missing_owners,
        sealed_receipts=sealed,
    )
    row["families"] = families
    row["skillDir"] = str(skill_dir.relative_to(root).as_posix())
    row["digests"] = digests
    row["driver"] = {
        "adapterDigest": binding.get("adapterDigest"),
        "runtimeDigest": binding.get("runtimeDigest"),
        "kind": binding.get("kind"),
        "profileId": binding.get("profileId"),
    }
    row["run"] = run_payload
    return row


def qualify_initial_release_profiles(
    root: Path,
    *,
    declared: Sequence[Mapping[str, str]] | None = None,
    evidence_dir: Optional[Path] = None,
    execute: bool = True,
) -> dict[str, Any]:
    combinations = list(declared or INITIAL_RELEASE_PROFILES)
    if len(combinations) != 5:
        raise QualificationError("initial_release_profile_count_invalid")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in combinations:
        combo = combination_id(item["skillId"], item["version"], item["runtimeProfile"])
        if combo in seen:
            raise QualificationError(f"duplicate_combination:{combo}")
        seen.add(combo)
        if execute:
            row = run_combination(root, item, evidence_dir=evidence_dir)
        else:
            skill_dir = root / "skills" / item["skillId"]
            cases = case_records(skill_dir)
            families = classify_case_families(cases)
            source_version = _frontmatter_version(skill_dir / "SKILL.md")
            driver = resolve_driver(item["runtimeProfile"])
            missing = list(driver.binding(root).get("missingOwnerReceipts") or [])
            row = classify_combination(
                skill_id=item["skillId"],
                version=item["version"],
                runtime_profile=item["runtimeProfile"],
                source_version=source_version,
                compatible_profiles=_compatible_profiles(skill_dir),
                families=families,
                executable_case_ids=[c["id"] for c in cases if c.get("hasExecute")],
                missing_owner_receipts=missing,
                sealed_receipts=False,
            )
            row["families"] = families
            row["skillDir"] = str(skill_dir.relative_to(root).as_posix())
            row["digests"] = source_digests(skill_dir)
        rows.append(row)
    usable = [row["id"] for row in rows if row["lifecycle"] == USABLE]
    pending = [row["id"] for row in rows if row["lifecycle"] == EVAL_PENDING]
    quarantined = [row["id"] for row in rows if row["lifecycle"] == QUARANTINED]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": MATRIX_KIND,
        "complete": len(rows) == 5,
        "ok": len(rows) == 5 and not quarantined,
        "usableClaimed": False,
        "combinations": rows,
        "usable": usable,
        "evalPending": pending,
        "quarantined": quarantined,
        "issuerReceipt": inspect_issuer_receipt(),
        "sealedImageReceipt": inspect_sealed_image_receipt(),
        "isolatorReceipt": inspect_isolator_receipt(),
        "cursorOwnerReceipt": inspect_owner_receipt(root, CURSOR_MACOS),
    }


def missing_owner_receipt_evidence(root: Path) -> dict[str, Any]:
    """Named missing live receipts. Never claims usable or fabricates live proof."""
    return {
        "kind": "ed-03-missing-owner-receipts",
        "receipts": [
            inspect_owner_receipt(root, CURSOR_MACOS),
            inspect_issuer_receipt(),
            inspect_sealed_image_receipt(),
        ],
        "schemaVersion": SCHEMA_VERSION,
        "usableClaimed": False,
    }


def stamp_initial_execution_profiles(root: Path) -> dict[str, str]:
    """Refresh draft execution-profile hashes after suite/script edits."""
    written: dict[str, str] = {}
    for item in INITIAL_RELEASE_PROFILES:
        skill_dir = root / "skills" / item["skillId"]
        profile = stamp_execution_profile(
            skill_dir,
            runtime_profile_id=item["runtimeProfile"],
            lifecycle_state="eval_pending",
        )
        path = skill_dir / "references" / "execution-profile.json"
        path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written[item["skillId"]] = str(profile["profile_hash"])
    return written
