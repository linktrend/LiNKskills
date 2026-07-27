"""Certification gate: require observed evidence; reject prompt-only / fake judges."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional

from .judge import judge_is_rejected
from .models import CaseStatus, RubricDimension, SuiteResult
from .runner import weighted_score


@dataclass
class CertificationDecision:
    """Result of attempting to certify an execution-profile run."""

    certified: bool
    reason: str
    profile_hash: Optional[str] = None
    weighted_score: Optional[float] = None
    hard_fail_dimensions: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)


def _profile_hash(run: SuiteResult) -> str:
    payload = {
        "skill_id": run.skill_id,
        "suite_id": run.suite_id,
        "suite_version": run.suite_version,
        "suite_hash": run.suite_hash,
        "judge_kind": run.judge_kind,
        "toolchain": run.toolchain,
        "case_ids": [c.case_id for c in run.case_results],
        "statuses": [c.status.value for c in run.case_results],
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def compute_suite_scores(
    run: SuiteResult,
    rubric: Optional[list[RubricDimension]] = None,
) -> tuple[float, list[str], dict[str, float]]:
    """Compute weighted score and hard-fail dimensions from case judge scores."""
    dims = rubric or [
        RubricDimension(dimension=name, weight=1.0)
        for name in sorted({k for c in run.case_results for k in c.judge_scores})
    ]
    if not dims:
        # Fall back to recorded suite score.
        return float(run.weighted_score or 0.0), list(run.hard_fail_dimensions), dict(run.dimension_scores)

    totals = {d.dimension: 0.0 for d in dims}
    counts = {d.dimension: 0 for d in dims}
    for case in run.case_results:
        for dim in dims:
            if dim.dimension in case.judge_scores:
                totals[dim.dimension] += float(case.judge_scores[dim.dimension])
                counts[dim.dimension] += 1
    dimension_scores = {
        dim.dimension: (totals[dim.dimension] / counts[dim.dimension])
        if counts[dim.dimension]
        else 0.0
        for dim in dims
    }
    score, hard_dims = weighted_score(dimension_scores, dims)
    return score, hard_dims, dimension_scores


def certify_run(
    run: SuiteResult,
    judge: Any = None,
    *,
    rubric: Optional[list[RubricDimension]] = None,
    pass_threshold: Optional[float] = None,
) -> CertificationDecision:
    """Decide whether *run* may produce a certification for its execution profile.

    Hard rejects:
    - FakeJudge / PromptOnlyJudge (by type or kind)
    - any case with status not_executable_prompt_only
    - missing case results / missing observed evidence
    - failed / hard-fail / infrastructure cases
    - hard_fail_below dimension floors
    """
    score, hard_dims, dimension_scores = compute_suite_scores(run, rubric=rubric)
    evidence: dict[str, Any] = {
        "skill_id": run.skill_id,
        "suite_id": run.suite_id,
        "suite_hash": run.suite_hash,
        "judge_kind": run.judge_kind,
        "toolchain": dict(run.toolchain),
        "case_count": len(run.case_results),
        "weighted_score": score,
        "dimension_scores": dimension_scores,
        "hard_fail_dimensions": hard_dims,
    }

    if judge is not None and judge_is_rejected(judge):
        kind = getattr(judge, "kind", type(judge).__name__)
        return CertificationDecision(
            certified=False,
            reason=f"judge rejected for certification: {kind}",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
        )

    if run.judge_kind in {"fake", "prompt_only"}:
        return CertificationDecision(
            certified=False,
            reason=f"judge rejected for certification: {run.judge_kind}",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
        )

    if not run.case_results:
        return CertificationDecision(
            certified=False,
            reason="cannot certify: no case results",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
        )

    if run.has_prompt_only_cases:
        prompt_only_ids = [
            c.case_id
            for c in run.case_results
            if c.status == CaseStatus.NOT_EXECUTABLE_PROMPT_ONLY
        ]
        evidence["prompt_only_case_ids"] = prompt_only_ids
        return CertificationDecision(
            certified=False,
            reason=(
                "cannot certify: suite contains not_executable_prompt_only cases "
                f"({', '.join(prompt_only_ids)})"
            ),
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
        )

    for case in run.case_results:
        if case.status in {
            CaseStatus.FAILED,
            CaseStatus.HARD_FAIL,
            CaseStatus.INFRASTRUCTURE_ERROR,
        }:
            return CertificationDecision(
                certified=False,
                reason=f"cannot certify: case {case.case_id!r} status={case.status.value}",
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
            )
        if not case.has_observed_evidence:
            return CertificationDecision(
                certified=False,
                reason=f"cannot certify: case {case.case_id!r} lacks observed output evidence",
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
            )
        if not case.evidence and not case.evidence_meta:
            return CertificationDecision(
                certified=False,
                reason=f"cannot certify: case {case.case_id!r} missing evidence artifacts",
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
            )

    if hard_dims:
        return CertificationDecision(
            certified=False,
            reason=f"cannot certify: hard_fail_below on {', '.join(hard_dims)}",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
        )

    threshold = pass_threshold
    if threshold is None:
        # Use runner's pass flag when threshold not supplied.
        if not run.passed:
            return CertificationDecision(
                certified=False,
                reason="cannot certify: run did not pass suite threshold",
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
            )
    elif score < threshold:
        return CertificationDecision(
            certified=False,
            reason=f"cannot certify: weighted_score {score:.4f} < pass_threshold {threshold:.4f}",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
        )

    profile = _profile_hash(run)
    evidence["profile_hash"] = profile
    return CertificationDecision(
        certified=True,
        reason=(
            "certified: observed outputs, deterministic checks, "
            "and independent judge evidence present"
        ),
        profile_hash=profile,
        weighted_score=score,
        hard_fail_dimensions=hard_dims,
        evidence=evidence,
    )
