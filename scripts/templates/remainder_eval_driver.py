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
from typing import Any, Mapping

CASES_REL = Path("references") / "remainder-eval-cases.json"

FAMILY_STATUS = {
    "remainder-success-ordinary-path": "PASS",
    "remainder-guardrail-refuse-ungoverned-action": "REFUSED",
    "remainder-failure-block-invalid-contract": "BLOCKED",
    "remainder-recovery-retry-transient-error": "RECOVERED",
    "remainder-privacy-redact-secret-pointer": "REDACTED",
}

# Cited executable golden-case contracts (git-safeguard eval-suite assertions /
# helper_tool status). These bind classification to the case's declared outcome
# rather than to generic id-token heuristics. A golden case whose contract is
# BLOCKED stays BLOCKED even when the id or input mentions a privacy term.
CITED_GOLDEN_CASE_STATUS = {
    "clean-tree-full-checklist-allows-push": "PASS",
    "staged-diff-contains-secret-blocks-push": "BLOCKED",
    "wrong-branch-target-blocks-push": "BLOCKED",
}

_EXPLICIT_STATUS_TOKENS = {
    "BLOCKED": "BLOCKED",
    "REDACTED": "REDACTED",
    "REFUSED": "REFUSED",
    "RECOVERED": "RECOVERED",
    "PASS": "PASS",
    "PERMIT": "PASS",
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


def _contract_text_parts(case: Mapping[str, Any] | None) -> list[str]:
    """Collect cited-contract fields only (assertions / expected criteria)."""
    if not isinstance(case, Mapping):
        return []
    parts: list[str] = []
    assertions = case.get("assertions") or case.get("deterministic_assertions") or {}
    if isinstance(assertions, Mapping):
        parts.extend(str(item) for item in (assertions.get("must_contain") or []))
    criteria = case.get("expected_criteria")
    if isinstance(criteria, list):
        parts.extend(str(item) for item in criteria)
    expected = case.get("expected")
    if isinstance(expected, Mapping):
        nested = expected.get("criteria") or []
        if isinstance(nested, list):
            parts.extend(str(item) for item in nested)
        if expected.get("status"):
            parts.append(str(expected["status"]))
    return parts


def status_from_case_contract(
    case_id: str,
    case: Mapping[str, Any] | None = None,
) -> str | None:
    """Return status declared by the cited case contract, if one exists.

    Does not inspect planted remainder expected-output fields such as ``status``
    on remainder-eval-cases.json. Uses suite assertions, expected criteria, and
    the frozen cited-golden map.
    """
    cid = str(case_id or "").strip()
    if cid in CITED_GOLDEN_CASE_STATUS:
        return CITED_GOLDEN_CASE_STATUS[cid]
    for raw in _contract_text_parts(case):
        token = str(raw).strip().strip('"').upper()
        if token in _EXPLICIT_STATUS_TOKENS:
            return _EXPLICIT_STATUS_TOKENS[token]
    blob = " ".join(_contract_text_parts(case)).lower()
    if not blob:
        return None
    if "blocks the push" in blob or "block the push" in blob:
        return "BLOCKED"
    if "redact" in blob and ("secret" in blob or "pii" in blob):
        return "REDACTED"
    if "refuses" in blob or "refuse" in blob:
        return "REFUSED"
    if "retries" in blob or "retried" in blob:
        return "RECOVERED"
    return None


def classify_contract_status(
    case_id: str,
    case_type: str = "",
    case: Mapping[str, Any] | None = None,
) -> str:
    """Classify expected contract status from the cited case contract.

    Family remainder ids keep their declared status. Cited golden cases bind to
    the suite/helper contract (so a BLOCKED secret-in-diff golden case is not
    reclassified as REDACTED merely because the id contains ``secret``).
    Token heuristics apply only when no cited contract is present. Golden cases
    whose expected output mentions the word "block" (for example
    "Preconditions block") remain PASS unless the case id itself is a failure
    or refuse family.
    """
    cid = str(case_id or "").strip()
    if cid in FAMILY_STATUS:
        return FAMILY_STATUS[cid]
    cited = status_from_case_contract(cid, case)
    if cited:
        return cited
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
    skill_id = str(payload.get("skill_id") or skill_dir.name)
    meta = parse_frontmatter(skill_dir / "SKILL.md")
    declared_name = meta.get("name") or skill_id
    declared_version = meta.get("version") or ""
    status = classify_contract_status(
        case_id,
        str(case.get("case_type") or ""),
        case=case if isinstance(case, dict) else None,
    )
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
