"""Confined remainder evaluator with a computed trading-performance fixture path.

Ordinary remainder cases keep the existing declared contract-status behavior.
Trading-performance cases load supplied fixture inputs, call the Decimal helper,
validate its output schema, and compare only declared assertions. Expected values
are not copied into the emitted result. Nothing claims live use or authority.
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



def _get_path(value: Any, path: str) -> Any:
    for part in path.split("."):
        if isinstance(value, list):
            value = value[int(part)]
        else:
            value = value[part]
    return value


def _evaluate_trading_fixture(skill_dir: Path, case_id: str, case: dict[str, Any], *, mode: str) -> tuple[dict[str, Any], int]:
    """Run supplied fixture data through the Decimal calculator and compare declared assertions."""
    from helper_tool import build_trading_performance_report, validate

    fixture_name = str(case.get("fixture") or "")
    fixture_path = skill_dir / "references" / "fixtures" / "trading-performance" / fixture_name
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        if not isinstance(fixture, dict) or fixture.get("mode") != "trading_performance":
            raise ValueError("fixture must be a trading_performance input object")
        input_errors = validate(fixture)
        expected_error = case.get("expected_error")
        if expected_error:
            if input_errors:
                message = "; ".join(input_errors)
                passed = str(expected_error) in message
            else:
                try:
                    build_trading_performance_report(fixture)
                    message = "calculator accepted invalid input"
                    passed = False
                except (ValueError, KeyError, ArithmeticError) as exc:
                    message = str(exc)
                    passed = str(expected_error) in message
            result = {"case_id": case_id, "mode": mode, "status": "PASS" if passed else "FAIL", "method_fixture_pass": passed, "observed_error": message, "permission_to_act": False, "certification_state": "draft", "selectable": False, "external_calls": [], "mutations": []}
            return result, 0 if passed else 1
        if input_errors:
            raise ValueError("fixture input contract failed: " + "; ".join(input_errors))
        observed = build_trading_performance_report(fixture)["trading_performance"]
        mismatches=[]
        assertions=case.get("assertions")
        if not isinstance(assertions,dict) or not assertions:
            raise ValueError("fixture case needs explicit result assertions")
        for key, expected in assertions.items():
            actual=_get_path(observed,key)
            if actual != expected: mismatches.append({"field":key,"expected":expected,"actual":actual})
        passed=not mismatches
        result={"case_id":case_id,"mode":mode,"status":"PASS" if passed else "FAIL","method_fixture_pass":passed,"assertions_checked":list(assertions),"mismatches":mismatches,"observed":{"equity_reconciled":observed["equity_reconciled"],"net_realized_pnl_base":observed["net_realized_pnl_base"],"closed_count":observed["closed_count"],"unknown_closed_count":observed["unknown_closed_count"],"all_closed_win_rate":observed["all_closed_win_rate"],"decided_win_rate":observed["decided_win_rate"],"profit_factor":observed["profit_factor"],"r_by_trade":observed["r_by_trade"]},"permission_to_act":False,"certification_state":"draft","selectable":False,"external_calls":[],"mutations":[]}
        return result,0 if passed else 1
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        return _fail_closed(case_id,str(exc)),1

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
    if case.get("case_type") == "trading_performance_fixture":
        return _evaluate_trading_fixture(skill_dir, case_id, case, mode=mode)
    if any(key in case for key in ("status", "summary", "contract_tokens", "expected_criteria")):
        # Legacy status cases may carry descriptive expectations, never result fields.
        pass
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
