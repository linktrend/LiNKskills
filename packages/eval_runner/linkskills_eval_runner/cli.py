"""CLI for the LiNKskills Eval Runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from .certify import certify_run
from .executor import compute_skill_release_hash
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
    skill_dir = Path(args.skill_dir).resolve() if args.skill_dir else None
    skill_release_hash = args.skill_release_hash
    if skill_release_hash is None and skill_dir is not None:
        skill_release_hash = compute_skill_release_hash(skill_dir)
    result = run_suite(
        suite,
        judge=judge,
        toolchain=toolchain,
        skill_dir=skill_dir,
        skill_release_hash=skill_release_hash,
    )
    decision = certify_run(
        result,
        judge=judge,
        rubric=suite.rubric,
        pass_threshold=suite.pass_threshold,
        expected_skill_release_hash=skill_release_hash,
    )
    payload = {
        "skill_id": result.skill_id,
        "suite_id": result.suite_id,
        "suite_version": result.suite_version,
        "suite_hash": result.suite_hash,
        "skill_release_hash": decision.skill_release_hash or skill_release_hash,
        "judge_kind": result.judge_kind,
        "weighted_score": decision.weighted_score if decision.weighted_score is not None else result.weighted_score,
        "dimension_scores": result.dimension_scores,
        "hard_fail_dimensions": decision.hard_fail_dimensions,
        "passed": result.passed,
        "certifiable": result.certifiable,
        "certified": decision.certified,
        "certify_reason": decision.reason,
        "profile_hash": decision.profile_hash,
        "receipt_hashes": decision.receipt_hashes,
        "execution_receipts": result.execution_receipts,
        "reasons": result.reasons,
        "toolchain": result.toolchain,
        "cases": [
            {
                "case_id": c.case_id,
                "status": c.status.value,
                "reason": c.reason,
                "has_observed_evidence": c.has_observed_evidence,
                "evidence_source": c.evidence_source,
                "case_score": c.case_score,
                "judge_scores": c.judge_scores,
                "execution_receipt": c.execution_receipt,
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


def _cmd_qualify_ed03(args: argparse.Namespace) -> int:
    import subprocess

    from .ed03 import qualify_initial_release_profiles

    root = Path(args.root).resolve()
    evidence_dir = (root / args.evidence_dir).resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    matrix = qualify_initial_release_profiles(
        root,
        evidence_dir=None if args.source_only else evidence_dir,
        execute=not args.source_only,
    )
    identity = {
        "repository": "linktrend/LiNKskills",
        "ref": None,
        "commit": None,
        "tree": None,
    }
    try:
        identity["ref"] = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, text=True
        ).strip()
        identity["commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        identity["tree"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    matrix["sourceIdentity"] = identity
    text = json.dumps(matrix, indent=2, sort_keys=True) + "\n"
    (evidence_dir / "qualification-matrix.json").write_text(text, encoding="utf-8")
    (evidence_dir / "identity.json").write_text(
        json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(text, end="")
    return 0 if matrix.get("complete") else 1


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
    run_p.add_argument(
        "--skill-dir",
        default=None,
        help="Immutable skill-release directory used to compute skill_release_hash",
    )
    run_p.add_argument(
        "--skill-release-hash",
        default=None,
        help="Explicit skill_release_hash pin (overrides --skill-dir hash)",
    )
    run_p.add_argument("--output", "-o", default=None, help="Write JSON result to path")
    run_p.add_argument(
        "--allow-uncertified",
        action="store_true",
        help="Exit 0 when the suite passes even if certification is refused",
    )
    run_p.set_defaults(func=_cmd_run)

    q_p = sub.add_parser(
        "qualify-ed03",
        help="Run confined consumer-profile qualification for the five initial releases",
    )
    q_p.add_argument("--root", default=".", help="Repository root")
    q_p.add_argument(
        "--evidence-dir",
        default="evidence/end-to-end-delivery/ed-03",
        help="Immutable evidence output directory",
    )
    q_p.add_argument(
        "--source-only",
        action="store_true",
        help="Classify suites without executing cases (never usable)",
    )
    q_p.set_defaults(func=_cmd_qualify_ed03)
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
