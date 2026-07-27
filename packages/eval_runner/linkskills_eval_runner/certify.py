"""Certification gate: require immutable executor receipts; reject suite-authored outputs."""

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
    receipt_hashes: list[str] = field(default_factory=list)


def _profile_hash(run: SuiteResult) -> str:
    payload = {
        "case_ids": [c.case_id for c in run.case_results],
        "judge_kind": run.judge_kind,
        "receipt_hashes": sorted(
            (c.execution_receipt or {}).get("receipt_hash") or ""
            for c in run.case_results
        ),
        "skill_id": run.skill_id,
        "statuses": [c.status.value for c in run.case_results],
        "suite_hash": run.suite_hash,
        "suite_id": run.suite_id,
        "suite_version": run.suite_version,
        "toolchain": run.toolchain,
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


def _receipt_valid(receipt: Any) -> bool:
    if not isinstance(receipt, dict):
        return False
    required = (
        "receipt_hash",
        "case_id",
        "skill_id",
        "suite_hash",
        "skill_release_hash",
        "execution_profile_hash",
        "stdout_hash",
        "stderr_hash",
        "tool_calls",
        "environment",
        "evidence_source",
        "executor_version",
    )
    if any(not receipt.get(key) and receipt.get(key) != 0 for key in required):
        # exit_code may be 0; evidence_source must be executor
        pass
    for key in required:
        if key not in receipt:
            return False
    if receipt.get("evidence_source") != "executor":
        return False
    if not receipt.get("receipt_hash"):
        return False
    # Recompute integrity from sealed payload fields.
    from .receipt import ExecutionReceipt, ToolCallRecord

    try:
        tool_calls = [
            ToolCallRecord(**tc) if isinstance(tc, dict) else tc
            for tc in (receipt.get("tool_calls") or [])
        ]
        rebuilt = ExecutionReceipt(
            receipt_id=str(receipt["receipt_id"]),
            case_id=str(receipt["case_id"]),
            skill_id=str(receipt["skill_id"]),
            suite_id=str(receipt.get("suite_id") or ""),
            suite_hash=str(receipt["suite_hash"]),
            skill_release_hash=str(receipt["skill_release_hash"]),
            execution_profile_hash=str(receipt["execution_profile_hash"]),
            environment=dict(receipt.get("environment") or {}),
            toolchain=dict(receipt.get("toolchain") or {}),
            tool_calls=tool_calls,
            exit_code=receipt.get("exit_code"),
            stdout_hash=str(receipt["stdout_hash"]),
            stderr_hash=str(receipt["stderr_hash"]),
            artifact_hashes=list(receipt.get("artifact_hashes") or []),
            started_at=str(receipt.get("started_at") or ""),
            finished_at=str(receipt.get("finished_at") or ""),
            executor_version=str(receipt.get("executor_version") or ""),
            evidence_source=str(receipt.get("evidence_source") or ""),
            receipt_hash="",
        )
        rebuilt.seal()
        return rebuilt.receipt_hash == receipt.get("receipt_hash")
    except Exception:  # noqa: BLE001
        return False


def certify_run(
    run: SuiteResult,
    judge: Any = None,
    *,
    rubric: Optional[list[RubricDimension]] = None,
    pass_threshold: Optional[float] = None,
) -> CertificationDecision:
    """Decide whether *run* may produce a certification for its execution profile.

    Hard rejects:
    - FakeJudge / PromptOnlyJudge
    - prompt-only or suite-authored-output cases
    - missing/invalid immutable execution receipts
    - evidence_source other than executor
    - failed / hard-fail / infrastructure cases
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
        "execution_receipt_count": len(run.execution_receipts),
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

    blocked_ids = [
        c.case_id
        for c in run.case_results
        if c.status
        in {
            CaseStatus.NOT_EXECUTABLE_PROMPT_ONLY,
            CaseStatus.INVALID_EMBEDDED_OUTPUT,
        }
    ]
    if blocked_ids:
        evidence["blocked_case_ids"] = blocked_ids
        statuses = {
            c.case_id: c.status.value
            for c in run.case_results
            if c.case_id in blocked_ids
        }
        # Preserve legacy token for prompt-only rejection assertions.
        prompt_token = (
            "not_executable_prompt_only"
            if any(
                c.status == CaseStatus.NOT_EXECUTABLE_PROMPT_ONLY
                for c in run.case_results
                if c.case_id in blocked_ids
            )
            else "suite_authored_or_non_executable"
        )
        return CertificationDecision(
            certified=False,
            reason=(
                f"cannot certify: {prompt_token} cases "
                f"({', '.join(f'{cid}={statuses[cid]}' for cid in blocked_ids)})"
            ),
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
        )

    receipt_hashes: list[str] = []
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
        if case.evidence_source != "executor":
            return CertificationDecision(
                certified=False,
                reason=(
                    f"cannot certify: case {case.case_id!r} evidence_source="
                    f"{case.evidence_source!r} (executor required)"
                ),
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
            )
        if case.evidence_meta.get("suite_authored_output_used_as_evidence"):
            return CertificationDecision(
                certified=False,
                reason=(
                    f"cannot certify: case {case.case_id!r} used suite-authored "
                    "output as evidence"
                ),
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
            )
        if not case.has_observed_evidence:
            return CertificationDecision(
                certified=False,
                reason=f"cannot certify: case {case.case_id!r} lacks executor evidence",
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
            )
        if not _receipt_valid(case.execution_receipt):
            return CertificationDecision(
                certified=False,
                reason=(
                    f"cannot certify: case {case.case_id!r} missing/invalid "
                    "immutable execution receipt"
                ),
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
            )
        receipt_hashes.append(str(case.execution_receipt.get("receipt_hash")))

    if hard_dims:
        return CertificationDecision(
            certified=False,
            reason=f"cannot certify: hard_fail_below on {', '.join(hard_dims)}",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
            receipt_hashes=receipt_hashes,
        )

    threshold = pass_threshold
    if threshold is None:
        if not run.passed:
            return CertificationDecision(
                certified=False,
                reason="cannot certify: run did not pass suite threshold",
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
                receipt_hashes=receipt_hashes,
            )
    elif score < threshold:
        return CertificationDecision(
            certified=False,
            reason=f"cannot certify: weighted_score {score:.4f} < pass_threshold {threshold:.4f}",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
            receipt_hashes=receipt_hashes,
        )

    profile = _profile_hash(run)
    evidence["profile_hash"] = profile
    evidence["receipt_hashes"] = receipt_hashes
    return CertificationDecision(
        certified=True,
        reason=(
            "certified: executor receipts bind case, release, tool, profile, "
            "environment/toolchain, and collected evidence"
        ),
        profile_hash=profile,
        weighted_score=score,
        hard_fail_dimensions=hard_dims,
        evidence=evidence,
        receipt_hashes=receipt_hashes,
    )
