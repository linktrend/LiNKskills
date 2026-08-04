#!/usr/bin/env python3
"""Audit all skills/*/references/eval-suite.yaml for Phase 1 readiness findings."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "evidence" / "phase1" / "suite-audit.json"

CASE_CLASSES = (
    "golden",
    "edge",
    "negative",
    "adversarial",
    "regression",
    "routing",
    "tool_failure",
    "compatibility",
    "efficiency",
    "side_effect_safety",
)


def _load_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        raise RuntimeError("PyYAML is required for suite audit")
    return yaml.safe_load(text)


def _scenarios(doc: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("scenarios", "cases"):
        value = doc.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    return []


def _has_deterministic_assertions(scenarios: list[dict[str, Any]]) -> bool:
    for sc in scenarios:
        assertions = sc.get("assertions") or sc.get("deterministic_assertions")
        if isinstance(assertions, dict) and assertions:
            return True
        if isinstance(assertions, list) and assertions:
            return True
    return False


def _has_hard_fail(doc: dict[str, Any], scenarios: list[dict[str, Any]]) -> bool:
    if doc.get("hard_failure_conditions"):
        return True
    for item in doc.get("rubric") or []:
        if isinstance(item, dict) and item.get("hard_fail_below") is not None:
            return True
    for sc in scenarios:
        if sc.get("hard_fail_on"):
            return True
    return False


def _case_classes_present(scenarios: list[dict[str, Any]]) -> list[str]:
    present: set[str] = set()
    for sc in scenarios:
        ctype = sc.get("case_type") or sc.get("type") or sc.get("class")
        if isinstance(ctype, str) and ctype in CASE_CLASSES:
            present.add(ctype)
            continue
        # Heuristic from scenario id/name for legacy suites.
        blob = " ".join(
            str(sc.get(k, "")) for k in ("id", "case_id", "name", "input")
        ).lower()
        if "guardrail" in blob or "must-block" in blob or "negative" in blob:
            present.add("negative")
        elif "routing" in blob:
            present.add("routing")
        elif "regression" in blob:
            present.add("regression")
        elif "edge" in blob:
            present.add("edge")
        elif "adversarial" in blob:
            present.add("adversarial")
        elif "tool" in blob and "fail" in blob:
            present.add("tool_failure")
        else:
            present.add("golden")
    return sorted(present)


def audit_suite(path: Path) -> dict[str, Any]:
    skill_id = path.parents[1].name
    finding: dict[str, Any] = {
        "skill_id": skill_id,
        "suite_path": str(path.relative_to(REPO_ROOT)),
        "exists": path.is_file(),
        "parse_ok": False,
        "structure_ok": False,
        "scenario_count": 0,
        "has_rubric": False,
        "has_pass_threshold": False,
        "has_deterministic_assertions": False,
        "has_hard_fail": False,
        "case_classes_present": [],
        "case_classes_missing": list(CASE_CLASSES),
        "readiness": "not_ready",
        "issues": [],
    }
    if not path.is_file():
        finding["issues"].append("missing eval-suite.yaml")
        return finding

    try:
        doc = _load_yaml(path)
    except Exception as exc:  # noqa: BLE001
        finding["issues"].append(f"yaml_parse_error: {exc}")
        return finding

    if not isinstance(doc, dict):
        finding["issues"].append("suite root must be a mapping")
        return finding

    finding["parse_ok"] = True
    scenarios = _scenarios(doc)
    finding["scenario_count"] = len(scenarios)
    finding["has_rubric"] = isinstance(doc.get("rubric"), list) and bool(doc.get("rubric"))
    finding["has_pass_threshold"] = doc.get("pass_threshold") is not None
    finding["has_deterministic_assertions"] = _has_deterministic_assertions(scenarios)
    finding["has_hard_fail"] = _has_hard_fail(doc, scenarios)
    present = _case_classes_present(scenarios)
    finding["case_classes_present"] = present
    finding["case_classes_missing"] = [c for c in CASE_CLASSES if c not in present]

    if not finding["has_rubric"]:
        finding["issues"].append("missing rubric")
    if not finding["has_pass_threshold"]:
        finding["issues"].append("missing pass_threshold")
    if finding["scenario_count"] < 1:
        finding["issues"].append("no scenarios/cases")
    if not finding["has_deterministic_assertions"]:
        finding["issues"].append("no deterministic assertions")
    if not finding["has_hard_fail"]:
        finding["issues"].append("no hard_fail signals")

    finding["structure_ok"] = (
        finding["has_rubric"]
        and finding["has_pass_threshold"]
        and finding["scenario_count"] >= 1
    )

    if finding["structure_ok"] and finding["has_deterministic_assertions"] and finding["has_hard_fail"]:
        finding["readiness"] = "ready_for_runner"
    elif finding["structure_ok"]:
        finding["readiness"] = "baseline_incomplete"
    else:
        finding["readiness"] = "not_ready"
    return finding


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out = Path(argv[0]) if argv else DEFAULT_OUT
    suite_paths = sorted((REPO_ROOT / "skills").glob("*/references/eval-suite.yaml"))
    findings = [audit_suite(path) for path in suite_paths]

    # Also report skills missing suites entirely.
    for skill_dir in sorted((REPO_ROOT / "skills").iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        suite = skill_dir / "references" / "eval-suite.yaml"
        if not suite.is_file():
            findings.append(audit_suite(suite))

    findings.sort(key=lambda f: f["skill_id"])
    summary = {
        "schema_version": "0.1",
        "suite_count": len(findings),
        "ready_for_runner": sum(1 for f in findings if f["readiness"] == "ready_for_runner"),
        "baseline_incomplete": sum(1 for f in findings if f["readiness"] == "baseline_incomplete"),
        "not_ready": sum(1 for f in findings if f["readiness"] == "not_ready"),
        "with_deterministic_assertions": sum(1 for f in findings if f["has_deterministic_assertions"]),
        "with_hard_fail": sum(1 for f in findings if f["has_hard_fail"]),
    }
    report = {"summary": summary, "findings": findings}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out} ({summary['suite_count']} suites)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
