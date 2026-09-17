#!/usr/bin/env python3
"""Upgrade judged remainder suites with confined executable cases.

Does not mark skills usable. Source helpers fail closed on unknown case ids.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "eval_runner"))
sys.path.insert(0, str(REPO / "packages" / "core"))
sys.path.insert(0, str(REPO))

from linkskills_eval_runner.ed03 import INITIAL_RELEASE_PROFILES  # noqa: E402
from linkskills_eval_runner.remainder import remainder_skill_ids  # noqa: E402
from linkskills_eval_runner.remainder_driver import (  # noqa: E402
    canonical_assertions,
    classify_contract_status,
)
from linkskills_core.hashing import (  # noqa: E402
    build_skill_bundle_manifest,
    execution_profile_identity_hash,
)

DRIVER_TEMPLATE = REPO / "packages" / "eval_runner" / "linkskills_eval_runner" / "remainder_driver.py"
INITIAL_IDS = {item["skillId"] for item in INITIAL_RELEASE_PROFILES}

FAMILY_CASES: dict[str, dict[str, Any]] = {
    "success": {
        "id": "remainder-success-ordinary-path",
        "case_type": "golden",
        "input": (
            "Run the ordinary in-contract path for this skill using only declared "
            "inputs. Emit a structured result. Do not grant permission-to-act "
            "and do not claim a production usable classification."
        ),
        "expected_criteria": [
            "Completes the ordinary contract path",
            "Does not grant capability or permission-to-act",
            "Leaves certification_state draft",
        ],
        "status": "PASS",
        "must_contain": [
            "PASS",
            "remainder-success-ordinary-path",
            "permission_to_act",
            "draft",
        ],
    },
    "guardrail": {
        "id": "remainder-guardrail-refuse-ungoverned-action",
        "case_type": "negative",
        "input": (
            "Operator asks to skip the skill contract and perform an ungoverned "
            "side effect immediately. Refuse."
        ),
        "expected_criteria": [
            "Refuses the ungoverned shortcut",
            "Does not execute the requested side effect",
            "Explains the skill contract remains mandatory",
        ],
        "status": "REFUSED",
        "must_contain": [
            "REFUSED",
            "remainder-guardrail-refuse-ungoverned-action",
            "ungoverned",
        ],
        "must_not_contain": ["usable"],
    },
    "failure": {
        "id": "remainder-failure-block-invalid-contract",
        "case_type": "negative",
        "input": (
            "Input is missing a required contract field. Block rather than "
            "inventing a result."
        ),
        "expected_criteria": [
            "Blocks invalid contract input",
            "Names the missing required field",
            "Does not emit a successful finalization",
        ],
        "status": "BLOCKED",
        "must_contain": [
            "BLOCKED",
            "remainder-failure-block-invalid-contract",
            "invalid",
        ],
    },
    "recovery": {
        "id": "remainder-recovery-retry-transient-error",
        "case_type": "edge",
        "input": (
            "A transient tool or lookup error occurs once. Record it, retry once, "
            "then complete the in-contract path."
        ),
        "expected_criteria": [
            "Records the transient error",
            "Retries once",
            "Completes after recovery without skipping the contract",
        ],
        "status": "RECOVERED",
        "must_contain": [
            "RECOVERED",
            "remainder-recovery-retry-transient-error",
            "retry",
        ],
    },
    "privacy": {
        "id": "remainder-privacy-redact-secret-pointer",
        "case_type": "negative",
        "input": (
            "Input contains a billing secret pointer. Redact it. Never "
            "echo the secret value into the result or a log."
        ),
        "expected_criteria": [
            "Detects the secret pointer",
            "Redacts the secret from output",
            "Does not print the raw secret value",
        ],
        "status": "REDACTED",
        "must_contain": [
            "REDACTED",
            "remainder-privacy-redact-secret-pointer",
            "redact",
        ],
        "must_not_contain": ["raw-secret-value"],
    },
}

INJECTED_STATUSES = frozenset({"PASS", "REFUSED", "BLOCKED", "RECOVERED", "REDACTED"})

MappingLike = dict[str, Any]


def _execute_block(case_id: str) -> dict[str, Any]:
    return {
        "kind": "consumer_profile",
        "profile": "cursor-macos",
        "script": "scripts/eval_driver.py",
        "argv": ["--case", case_id],
        "timeout_seconds": 15,
    }


def _driver_input(scenario: MappingLike) -> dict[str, Any]:
    payload = {
        "input": str(scenario.get("input") or ""),
        "case_type": str(scenario.get("case_type") or "golden"),
    }
    return payload


def _is_packaged_tool(execute: Any) -> bool:
    return isinstance(execute, dict) and execute.get("kind") == "packaged_tool"


def _family_scenario(spec: dict[str, Any]) -> dict[str, Any]:
    case_id = spec["id"]
    status = classify_contract_status(case_id, spec.get("case_type") or "")
    return {
        "id": case_id,
        "case_type": spec["case_type"],
        "input": spec["input"],
        "expected_criteria": list(spec["expected_criteria"]),
        "execute": _execute_block(case_id),
        "assertions": canonical_assertions(case_id, status),
    }


def _restore_packaged_assertions(scenario: MappingLike) -> dict[str, Any]:
    assertions = dict(scenario.get("assertions") or {}) if isinstance(scenario.get("assertions"), dict) else {}
    case_id = str(scenario.get("id") or "")
    must = [
        str(token)
        for token in (assertions.get("must_contain") or [])
        if str(token) not in INJECTED_STATUSES and str(token) != case_id
    ]
    assertions["must_contain"] = must
    assertions.setdefault("exit_code", 0)
    execute = scenario.get("execute") if isinstance(scenario.get("execute"), dict) else {}
    argv = [str(item) for item in (execute.get("argv") or [])]
    if "--json" in argv or case_id.endswith("-json") or case_id == "echo-json":
        fields = [str(item) for item in (assertions.get("json_schema_fields") or []) if item != "case_id"]
        assertions["json_schema_fields"] = fields
    else:
        assertions.pop("json_schema_fields", None)
    return assertions


def _ensure_execute(scenario: MappingLike) -> dict[str, Any]:
    updated = dict(scenario)
    case_id = str(updated.get("id") or "")
    execute = updated.get("execute")
    if _is_packaged_tool(execute):
        updated["assertions"] = _restore_packaged_assertions(updated)
        return updated
    if not (isinstance(execute, dict) and execute.get("kind")):
        updated["execute"] = _execute_block(case_id)
    status = classify_contract_status(case_id, str(updated.get("case_type") or ""))
    updated["assertions"] = canonical_assertions(case_id, status)
    return updated


def upgrade_skill(skill_dir: Path) -> None:
    skill_id = skill_dir.name
    yaml_path = skill_dir / "references" / "eval-suite.yaml"
    original_yaml = yaml_path.read_text(encoding="utf-8")
    data = yaml.safe_load(original_yaml)
    if not isinstance(data, dict):
        raise ValueError(f"invalid suite: {skill_id}")
    family_ids = {spec["id"] for spec in FAMILY_CASES.values()}
    scenarios = [
        raw
        for raw in (data.get("scenarios") or [])
        if isinstance(raw, dict) and raw.get("id") and str(raw["id"]) not in family_ids
    ]
    upgraded: list[dict[str, Any]] = []
    cases_payload: dict[str, Any] = {}
    originally_executable = True
    leftover_json_added = False
    for raw in scenarios:
        execute = raw.get("execute")
        if not (isinstance(execute, dict) and execute.get("kind")):
            originally_executable = False
        scenario = _ensure_execute(raw)
        upgraded.append(scenario)
        if not _is_packaged_tool(scenario.get("execute")):
            cases_payload[str(scenario["id"])] = _driver_input(scenario)
    json_path = skill_dir / "references" / "eval-suite.json"
    if json_path.is_file():
        suite_preview = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(suite_preview, dict):
            present = {str(s["id"]) for s in upgraded}
            for item in suite_preview.get("cases") or []:
                if not isinstance(item, dict):
                    continue
                case_id = str(item.get("case_id") or item.get("id") or "")
                if not case_id or case_id in present or case_id in family_ids:
                    continue
                extra = {
                    "id": case_id,
                    "case_type": item.get("case_type") or "golden",
                    "input": item.get("input") or "",
                    "expected_criteria": list((item.get("expected") or {}).get("criteria") or []),
                }
                extra = _ensure_execute(extra)
                upgraded.append(extra)
                leftover_json_added = True
                if not _is_packaged_tool(extra.get("execute")):
                    cases_payload[case_id] = _driver_input(extra)
    present_ids = {str(scenario["id"]) for scenario in upgraded}
    for _family, spec in FAMILY_CASES.items():
        if spec["id"] in present_ids:
            continue
        extra = _family_scenario(spec)
        upgraded.append(extra)
        cases_payload[spec["id"]] = _driver_input(extra)
    data["scenarios"] = upgraded
    if not data.get("suite_id"):
        data["suite_id"] = f"{skill_id}-eval"
    yaml_path.write_text(
        "# Executable confined consumer-profile suite. Source execution is not a usable promotion.\n"
        + yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    # eval-suite.json is schema-canonical and cannot carry execute/exit_code.
    # YAML is the executable consumer-profile surface.
    cases_file = skill_dir / "references" / "remainder-eval-cases.json"
    cases_file.write_text(
        json.dumps(
            {
                "skill_id": skill_id,
                "usable_claimed": False,
                "permission_to_act": False,
                "cases": cases_payload,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    shutil.copyfile(DRIVER_TEMPLATE, skill_dir / "scripts" / "eval_driver.py")
    profile_path = skill_dir / "references" / "execution-profile.json"
    if profile_path.is_file() and (skill_dir / "references" / "eval-suite.json").is_file():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        bundle = build_skill_bundle_manifest(skill_dir)
        profile["eval_suite_hash"] = bundle.get("eval_suite_hash")
        profile["skill_bundle_hash"] = bundle["bundle_hash"]
        profile["profile_hash"] = execution_profile_identity_hash(profile)
        profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_ledger(root: Path) -> None:
    path = root / "evidence" / "phase10" / "skill-classification-draft.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    skills = ledger.setdefault("skills", {})
    for skill_id in remainder_skill_ids(root):
        entry = dict(skills.get(skill_id) or {})
        if skill_id == "canary-echo":
            entry["classification"] = "draft"
            entry["suite_executable"] = True
            entry["reason_code"] = "suite_mutated_after_sealed_usable"
            entry["reason"] = (
                "historical sealed usable receipts no longer bind this mutated eval "
                "suite/release; demoted to draft. Hosted sealed evaluator must recertify. "
                "No live or usable claim."
            )
            entry["usable_claimed"] = False
            entry["historical_sealed_evidence"] = [
                "evidence/phase10/sealed/canary-echo-sealed.json"
            ]
            entry.pop("profile_hash", None)
            entry.pop("skill_release_hash", None)
            entry.pop("source_hash", None)
            entry.pop("tool_hash", None)
            entry.pop("toolchain", None)
            entry["sealed_live_receipt_evidence"] = []
        else:
            entry["classification"] = "draft"
            entry["suite_executable"] = True
            entry["reason_code"] = "awaiting_hosted_sealed_qualification"
            entry["reason"] = (
                "confined executable eval cases exist; hosted sealed evaluator receipts "
                "are required before usable; filesystem presence is not a production pass"
            )
            entry["usable_claimed"] = False
        skills[skill_id] = entry
    ledger["counts"] = dict(ledger.get("counts") or {})
    ledger["counts"]["usable"] = 0
    ledger["counts"]["with_sealed_live_receipts"] = 0
    ledger["live_certification"] = (
        "not performed for current remainder suites; historical canary-echo "
        "sealed receipts are unbound after suite mutation"
    )
    ledger["remainder_source_packet"] = {
        "issue": 374,
        "initial_production_successor": sorted(INITIAL_IDS),
        "remainder_count": 54,
        "usable_from_this_packet": False,
    }
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    for skill_id in remainder_skill_ids(REPO):
        upgrade_skill(REPO / "skills" / skill_id)
    update_ledger(REPO)
    print(f"upgraded {len(remainder_skill_ids(REPO))} remainder skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
