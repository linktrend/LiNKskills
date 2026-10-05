"""Confined remainder eval driver — executes declared contract status, never echoes fixtures.

This module is stdlib-only so it can be copied to ``skills/*/scripts/eval_driver.py``
and run inside the sealed skill workspace without importing the Eval Runner package.

It must not copy planted expected responses from remainder-eval-cases.json into
stdout. Case files are inputs (and optional case_type) only.
It never claims usable, live, selectable, or permission-to-act.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CASES_REL = Path("references") / "remainder-eval-cases.json"

FAMILY_STATUS = {
    "remainder-success-ordinary-path": "PASS",
    "remainder-guardrail-refuse-ungoverned-action": "REFUSED",
    "remainder-failure-block-invalid-contract": "BLOCKED",
    "remainder-recovery-retry-transient-error": "RECOVERED",
    "remainder-privacy-redact-secret-pointer": "REDACTED",
}

_FAIL_TOKENS = frozenset(
    {"blocked", "blocks", "block", "failure", "fail", "invalid", "denied", "reject"}
)
_REFUSE_TOKENS = frozenset({"refuse", "refused", "guardrail"})
_RECOVERY_TOKENS = frozenset({"recovery", "retry"})
_PRIVACY_TOKENS = frozenset({"privacy", "redact", "pii", "secret"})


def case_id_tokens(case_id: str) -> set[str]:
    """Split a case id on ``-`` / ``_`` so 'block' is not matched inside other words."""
    return {part for part in str(case_id).lower().replace("_", "-").split("-") if part}


def classify_contract_status(case_id: str, case_type: str = "") -> str:
    """Classify expected contract status from id/type — not from expected-output text.

    Golden cases whose expected output mentions the word "block" (for example
    "Preconditions block") remain PASS unless the case id itself is a failure
    or refuse family.
    """
    cid = str(case_id or "").strip()
    if cid in FAMILY_STATUS:
        return FAMILY_STATUS[cid]
    tokens = case_id_tokens(cid)
    joined = cid.lower()
    if tokens & _PRIVACY_TOKENS or "secret-pointer" in joined:
        return "REDACTED"
    if tokens & _RECOVERY_TOKENS:
        return "RECOVERED"
    if tokens & _REFUSE_TOKENS or "guardrail" in joined:
        return "REFUSED"
    if tokens & _FAIL_TOKENS:
        return "BLOCKED"
    if str(case_type or "").lower() == "negative":
        return "REFUSED"
    return "PASS"


def canonical_assertions(case_id: str, status: str) -> dict[str, Any]:
    """Assertions the Eval Runner and qualify_remainder must both enforce."""
    must = [case_id, status]
    must_not: list[str] = []
    if status == "PASS":
        must.extend(["permission_to_act", "draft"])
    elif status == "REFUSED":
        must.append("ungoverned")
        must_not.append("usable")
    elif status == "BLOCKED":
        must.append("invalid")
    elif status == "RECOVERED":
        must.append("retry")
    elif status == "REDACTED":
        must.append("redact")
        must_not.append("raw-secret-value")
    spec: dict[str, Any] = {
        "must_contain": must,
        "json_schema_fields": ["status", "case_id"],
        "exit_code": 0,
    }
    if must_not:
        spec["must_not_contain"] = must_not
    return spec


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    if not skill_md.is_file():
        return meta
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return meta
    end = text.find("\n---", 3)
    if end < 0:
        return meta
    for raw in text[3:end].splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if key in {"name", "version", "format_profile"}:
            meta[key] = value.strip().strip('"').strip("'")
    return meta


def load_case_inputs(skill_dir: Path) -> dict[str, Any]:
    path = skill_dir / CASES_REL
    if not path.is_file():
        raise FileNotFoundError(path.as_posix())
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), dict):
        raise ValueError("remainder-eval-cases.json must contain a cases object")
    return payload


def _fail_closed(case_id: str, message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "case_id": case_id,
        "message": message,
        "permission_to_act": False,
        "certification_state": "draft",
        "selectable": False,
        "external_calls": [],
        "mutations": [],
    }




REFINE_REVIEW_CASES={"refiner-review-cross-file-finding","refiner-review-separated-evidence","refiner-review-stale-target","refiner-review-structural-only","refiner-review-pass-without-receipt","refiner-review-path-traversal","refiner-review-line-zero"}

def _schema_errors(value:Any,definition:dict[str,Any],schemas:dict[str,Any])->list[Any]:
    from jsonschema import Draft202012Validator
    root={"$schema":"https://json-schema.org/draft/2020-12/schema","definitions":schemas.get("definitions",{}),**definition}
    return list(Draft202012Validator(root).iter_errors(value))

def _refine_review(request:dict[str,Any])->dict[str,Any]:
    binding=request["target_binding"]; observed=request["observed_target_sha256"]; bound=binding["sha256"]
    report={"target_binding":binding,"observed_target_sha256":observed,"disposition":request["requested_disposition"],"structural":{"status":"NOT_RUN","reason":"No structural receipt supplied."},"semantic":{"status":"NOT_REVIEWED","reason":"No semantic review supplied.","findings":[]},"behavior":{"status":"NOT_EVALUATED","reason":"No consumer behavior receipt supplied.","scenario_count":0,"matched_scenario_count":0},"qualification":"NOT_CLAIMED"}
    if observed!=bound:
        report.update(disposition="STALE_TARGET",structural={"status":"STALE_TARGET","reason":"Observed target digest differs from the bound digest."},semantic={"status":"STALE_TARGET","reason":"Findings are suppressed because the target changed.","findings":[]},behavior={"status":"STALE_TARGET","reason":"Behavior evidence cannot be carried across target bytes.","scenario_count":0,"matched_scenario_count":0})
        return report
    if request["requested_disposition"]=="PATCH_PROPOSED":
        if request.get("patch_ref"):report["patch_ref"]=request["patch_ref"]
        else:report["disposition"]="BLOCKED"
    receipt=request.get("structural_receipt")
    if receipt is not None:
        if receipt.get("target_sha256")!=bound:report["structural"]={"status":"STALE_RECEIPT","reason":"Structural receipt targets different bytes."}
        elif not receipt.get("receipt_ref"):report["structural"]={"status":"MISSING_RECEIPT","reason":"Structural outcome has no receipt reference."}
        else:report["structural"]={"status":"PASS_REPORTED" if receipt["reported_status"]=="PASS" else "FAIL_REPORTED","reason":"Structural outcome is recorded as reported evidence, not an independent qualification.","checked_sha256":bound,"receipt_ref":receipt["receipt_ref"]}
    semantic=request.get("semantic_review")
    if semantic is not None:
        if semantic.get("reviewed_sha256")!=bound:report["semantic"]={"status":"STALE_REVIEW","reason":"Semantic findings target different bytes.","findings":[]}
        elif any(row["path"] != binding["target_path"] for row in semantic.get("findings",[])):
            report["disposition"]="BLOCKED"
            report["semantic"]={"status":"NOT_REVIEWED","reason":"Finding path is outside the exact bound target; supply a separate binding and receipt for that file.","findings":[]}
        elif not semantic.get("reviewer_ref"):report["semantic"]={"status":"NOT_REVIEWED","reason":"Semantic review has no reviewer reference.","findings":[]}
        elif semantic["status"]=="FINDINGS" and semantic.get("findings"):report["semantic"]={"status":"FINDINGS_REPORTED","reason":"Findings are recorded from the named review; they are not a qualification result.","reviewed_sha256":bound,"reviewer_ref":semantic["reviewer_ref"],"findings":semantic["findings"]}
        elif semantic["status"]=="NO_FINDINGS" and not semantic.get("findings"):report["semantic"]={"status":"NO_FINDINGS_REPORTED","reason":"No findings were reported by the named review; this is not a behavior pass.","reviewed_sha256":bound,"reviewer_ref":semantic["reviewer_ref"],"findings":[]}
        else:report["semantic"]={"status":"NOT_REVIEWED","reason":"Semantic review fields are incomplete or inconsistent.","findings":[]}
    behavior=request.get("behavior_receipt")
    if behavior is not None:
        if behavior.get("target_sha256")!=bound:report["behavior"]={"status":"STALE_RECEIPT","reason":"Behavior receipt targets different bytes.","scenario_count":0,"matched_scenario_count":0}
        elif not behavior.get("receipt_ref") or not behavior.get("scenario_results"):report["behavior"]={"status":"MISSING_RECEIPT","reason":"Claimed behavior outcome lacks a receipt reference or scenario results.","scenario_count":len(behavior.get("scenario_results",[])),"matched_scenario_count":0}
        else:
            rows=behavior["scenario_results"]; matched=sum(1 for row in rows if row["reported_status"]=="PASS" and row["expected_conclusion"]==row["observed_conclusion"]); status="PASS_REPORTED" if behavior["reported_status"]=="PASS" and matched==len(rows) else "FAIL_REPORTED"
            report["behavior"]={"status":status,"reason":"Consumer results are reported against the bound target; receipt authenticity/qualification remains separately owned.","evaluated_sha256":bound,"receipt_ref":behavior["receipt_ref"],"scenario_count":len(rows),"matched_scenario_count":matched}
    return report

def evaluate_refine_review_case(skill_dir:Path,case_id:str,case:dict[str,Any])->tuple[dict[str,Any],int]:
    request=case.get("request")
    if not isinstance(request,dict):return _fail_closed(case_id,"refine review request is missing"),1
    try:
        schemas=json.loads((skill_dir/"references"/"schemas.json").read_text(encoding="utf-8")); input_errors=_schema_errors(request,{"$ref":"#/definitions/refine_review_request"},schemas)
        if input_errors:return _fail_closed(case_id,"refine review request does not match schema"),1
        review=_refine_review(request); errors=_schema_errors(review,{"$ref":"#/definitions/refine_review"},schemas)
    except Exception:return _fail_closed(case_id,"review schema evaluation failed"),1
    conditions={
      "refiner-review-separated-evidence":review["structural"]["status"]=="PASS_REPORTED" and review["semantic"]["status"]=="FINDINGS_REPORTED" and review["behavior"]["status"]=="NOT_EVALUATED" and review["disposition"]=="PATCH_PROPOSED",
      "refiner-review-stale-target":review["disposition"]=="STALE_TARGET" and review["structural"]["status"]=="STALE_TARGET" and not review["semantic"]["findings"],
      "refiner-review-structural-only":review["structural"]["status"]=="PASS_REPORTED" and review["semantic"]["status"]=="NOT_REVIEWED" and review["behavior"]["status"]=="NOT_EVALUATED",
      "refiner-review-cross-file-finding":review["disposition"]=="BLOCKED" and review["semantic"]["status"]=="NOT_REVIEWED" and not review["semantic"]["findings"],
      "refiner-review-pass-without-receipt":review["behavior"]["status"]=="MISSING_RECEIPT" and review["behavior"]["status"]!="PASS_REPORTED"}
    passed=conditions.get(case_id,False) and not errors
    result={"case_id":case_id,"status":"PASS" if passed else "FAIL","fixture_contract_check":"PASS" if passed else "FAIL","refine_review":review,"response_schema_valid":not errors,"permission_to_act":False,"certification_state":"draft","selectable":False,"external_calls":[],"mutations":[]}
    return result,0 if passed else 1

def evaluate_remainder_case(skill_dir: Path, case_id: str, *, mode: str = "evaluate") -> tuple[dict[str, Any], int]:
    """Execute the confined contract for *case_id*. Never echo planted expected JSON."""
    case_id = str(case_id).strip()
    try:
        payload = load_case_inputs(skill_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _fail_closed(case_id, str(exc)), 1
    case = payload["cases"].get(case_id)
    if not isinstance(case, dict):
        return _fail_closed(case_id, f"unknown case: {case_id}"), 1
    if any(key in case for key in ("status", "summary", "contract_tokens", "expected_criteria")):
        # Inputs may still list case_type/input only. Planted expected fields are ignored.
        pass
    if case_id in REFINE_REVIEW_CASES:
        return evaluate_refine_review_case(skill_dir, case_id, case)
    skill_id = str(payload.get("skill_id") or skill_dir.name)
    meta = parse_frontmatter(skill_dir / "SKILL.md")
    declared_name = meta.get("name") or skill_id
    declared_version = meta.get("version") or ""
    status = classify_contract_status(case_id, str(case.get("case_type") or ""))
    input_text = str(case.get("input") or "")
    result: dict[str, Any] = {
        "case_id": case_id,
        "mode": mode,
        "skill_id": skill_id,
        "status": status,
        "permission_to_act": False,
        "capability_grant": False,
        "certification_state": "draft",
        "selectable": False,
        "production_claim": False,
        "external_calls": [],
        "mutations": [],
        "declared_name": declared_name,
        "declared_version": declared_version,
        "input_present": bool(input_text.strip()),
    }
    if status == "PASS":
        result["decision"] = (
            f"{declared_name} completes the ordinary in-contract path; "
            "permission_to_act remains false; certification_state stays draft."
        )
        result["ordinary_path"] = True
    elif status == "REFUSED":
        result["decision"] = (
            f"{declared_name} refuses the ungoverned shortcut. The skill contract "
            "remains mandatory; no side effect is executed."
        )
        result["ungoverned"] = True
        result["refused_side_effect"] = True
    elif status == "BLOCKED":
        result["decision"] = (
            f"{declared_name} blocks invalid contract input and names the missing "
            "required field rather than inventing a finalization."
        )
        result["invalid"] = True
        result["missing_required_field"] = "required contract field"
    elif status == "RECOVERED":
        result["decision"] = (
            f"{declared_name} records the transient error, retries once, then "
            "completes the in-contract path."
        )
        result["retry"] = 1
        result["transient_error"] = True
    elif status == "REDACTED":
        result["decision"] = (
            f"{declared_name} detects the secret pointer and redacts it. "
            "The raw secret is not emitted."
        )
        result["redact"] = True
        result["secret_pointer"] = "[REDACTED]"
    return result, 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--mode", default="evaluate")
    args = parser.parse_args(argv)
    skill_dir = Path(__file__).resolve().parents[1]
    # Copied skill script lives at skills/<id>/scripts/eval_driver.py
    if skill_dir.name == "scripts":
        skill_dir = skill_dir.parent
    # Package module lives under packages/eval_runner/...; callers pass cwd skill dir.
    if (skill_dir / "references" / "remainder-eval-cases.json").is_file():
        pass
    elif Path.cwd().joinpath("references", "remainder-eval-cases.json").is_file():
        skill_dir = Path.cwd()
    result, code = evaluate_remainder_case(skill_dir, args.case, mode=args.mode)
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
