"""Certification gate: require immutable executor receipts; reject suite-authored outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .executor import is_unset_skill_release_hash
from .judge import judge_is_rejected
from .models import CaseStatus, RubricDimension, SuiteResult
from .runner import weighted_score


@dataclass
class CertificationDecision:
    """Result of attempting to certify an execution-profile run."""

    certified: bool
    reason: str
    profile_hash: Optional[str] = None
    skill_release_hash: Optional[str] = None
    weighted_score: Optional[float] = None
    hard_fail_dimensions: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    receipt_hashes: list[str] = field(default_factory=list)


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
        return (
            float(run.weighted_score or 0.0),
            list(run.hard_fail_dimensions),
            dict(run.dimension_scores),
        )

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
    for key in required:
        if key not in receipt:
            return False
    if receipt.get("evidence_source") != "executor":
        return False
    if not receipt.get("receipt_hash"):
        return False
    if is_unset_skill_release_hash(str(receipt.get("skill_release_hash") or "")):
        return False
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
    expected_skill_release_hash: Optional[str] = None,
) -> CertificationDecision:
    """Decide whether *run* may produce a certification for its execution profile."""
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
    release_hashes: set[str] = set()
    profile_hashes: set[str] = set()
    suite_hashes: set[str] = set()

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
        receipt = case.execution_receipt or {}
        release = str(receipt.get("skill_release_hash") or "")
        if is_unset_skill_release_hash(release):
            return CertificationDecision(
                certified=False,
                reason=(
                    f"cannot certify: case {case.case_id!r} skill_release_hash is "
                    "unset/placeholder (skill-release:unset cannot certify)"
                ),
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
            )
        if not _receipt_valid(receipt):
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
        receipt_hashes.append(str(receipt.get("receipt_hash")))
        release_hashes.add(release)
        profile_hashes.add(str(receipt.get("execution_profile_hash") or ""))
        suite_hashes.add(str(receipt.get("suite_hash") or ""))

    if len(release_hashes) != 1:
        return CertificationDecision(
            certified=False,
            reason="cannot certify: skill_release_hash is not identical across cases",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
            receipt_hashes=receipt_hashes,
        )
    release_hash = next(iter(release_hashes))
    evidence["skill_release_hash"] = release_hash

    if expected_skill_release_hash is not None:
        expected = str(expected_skill_release_hash).strip()
        if is_unset_skill_release_hash(expected):
            return CertificationDecision(
                certified=False,
                reason="cannot certify: expected_skill_release_hash is unset/placeholder",
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
                receipt_hashes=receipt_hashes,
                skill_release_hash=release_hash,
            )
        if release_hash != expected:
            return CertificationDecision(
                certified=False,
                reason=(
                    "cannot certify: skill_release_hash mismatch "
                    f"(receipt={release_hash!r} expected={expected!r})"
                ),
                weighted_score=score,
                hard_fail_dimensions=hard_dims,
                evidence=evidence,
                receipt_hashes=receipt_hashes,
                skill_release_hash=release_hash,
            )

    if len(profile_hashes) != 1 or not next(iter(profile_hashes)):
        return CertificationDecision(
            certified=False,
            reason="cannot certify: execution_profile_hash missing or inconsistent across cases",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
            receipt_hashes=receipt_hashes,
            skill_release_hash=release_hash,
        )
    profile_hash = next(iter(profile_hashes))

    if len(suite_hashes) != 1 or next(iter(suite_hashes)) != run.suite_hash:
        return CertificationDecision(
            certified=False,
            reason="cannot certify: suite_hash mismatch between run and receipts",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
            receipt_hashes=receipt_hashes,
            skill_release_hash=release_hash,
            profile_hash=profile_hash,
        )

    if hard_dims:
        return CertificationDecision(
            certified=False,
            reason=f"cannot certify: hard_fail_below on {', '.join(hard_dims)}",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
            receipt_hashes=receipt_hashes,
            skill_release_hash=release_hash,
            profile_hash=profile_hash,
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
                skill_release_hash=release_hash,
                profile_hash=profile_hash,
            )
    elif score < threshold:
        return CertificationDecision(
            certified=False,
            reason=f"cannot certify: weighted_score {score:.4f} < pass_threshold {threshold:.4f}",
            weighted_score=score,
            hard_fail_dimensions=hard_dims,
            evidence=evidence,
            receipt_hashes=receipt_hashes,
            skill_release_hash=release_hash,
            profile_hash=profile_hash,
        )

    evidence["profile_hash"] = profile_hash
    evidence["receipt_hashes"] = receipt_hashes
    return CertificationDecision(
        certified=True,
        reason=(
            "certified: executor receipts bind case, immutable skill release, "
            "deterministic execution profile, toolchain, and collected evidence"
        ),
        profile_hash=profile_hash,
        skill_release_hash=release_hash,
        weighted_score=score,
        hard_fail_dimensions=hard_dims,
        evidence=evidence,
        receipt_hashes=receipt_hashes,
    )
