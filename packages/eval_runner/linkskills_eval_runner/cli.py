"""CLI for the LiNKskills Eval Runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from .certify import certify_run
from .judge import FakeJudge, IndependentDeterministicJudge, PromptOnlyJudge
from .runner import YamlDependencyError, load_eval_suite, run_suite


def _build_judge(name: str):
    mapping = {
        "independent_deterministic": IndependentDeterministicJudge,
        "fake": FakeJudge,
        "prompt_only": PromptOnlyJudge,
    }
    try:
        return mapping[name]()
    except KeyError as exc:
        raise SystemExit(f"unknown judge: {name!r}; choose from {sorted(mapping)}") from exc


def _cmd_run(args: argparse.Namespace) -> int:
    suite = load_eval_suite(args.suite)
    judge = _build_judge(args.judge)
    toolchain = {}
    if args.toolchain_json:
        toolchain = json.loads(Path(args.toolchain_json).read_text(encoding="utf-8"))
    result = run_suite(suite, judge=judge, toolchain=toolchain)
    decision = certify_run(
        result,
        judge=judge,
        rubric=suite.rubric,
        pass_threshold=suite.pass_threshold,
    )
    payload = {
        "skill_id": result.skill_id,
        "suite_id": result.suite_id,
        "suite_version": result.suite_version,
        "suite_hash": result.suite_hash,
        "judge_kind": result.judge_kind,
        "weighted_score": decision.weighted_score if decision.weighted_score is not None else result.weighted_score,
        "dimension_scores": result.dimension_scores,
        "hard_fail_dimensions": decision.hard_fail_dimensions,
        "passed": result.passed,
        "certifiable": result.certifiable,
        "certified": decision.certified,
        "certify_reason": decision.reason,
        "profile_hash": decision.profile_hash,
        "reasons": result.reasons,
        "toolchain": result.toolchain,
        "cases": [
            {
                "case_id": c.case_id,
                "status": c.status.value,
                "reason": c.reason,
                "has_observed_evidence": c.has_observed_evidence,
                "case_score": c.case_score,
                "judge_scores": c.judge_scores,
                "assertions": [
                    {
                        "name": a.name,
                        "passed": a.passed,
                        "detail": a.detail,
                        "hard_fail": a.hard_fail,
                    }
                    for a in c.assertion_results
                ],
            }
            for c in result.case_results
        ],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if decision.certified or (result.passed and args.allow_uncertified) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="linkskills-eval",
        description="LiNKskills Eval Runner — deterministic observed-execution suites",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Load and run an eval-suite.yaml")
    run_p.add_argument("suite", help="Path to eval-suite.yaml")
    run_p.add_argument(
        "--judge",
        default="independent_deterministic",
        help="Judge adapter kind (fake/prompt_only are rejected by certifier)",
    )
    run_p.add_argument("--toolchain-json", default=None, help="Optional toolchain lock JSON")
    run_p.add_argument("--output", "-o", default=None, help="Write JSON result to path")
    run_p.add_argument(
        "--allow-uncertified",
        action="store_true",
        help="Exit 0 when the suite passes even if certification is refused",
    )
    run_p.set_defaults(func=_cmd_run)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except YamlDependencyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
