"""Eval suite and run result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class CaseStatus(str, Enum):
    """Outcome classification for a single eval case."""

    PASSED = "passed"
    FAILED = "failed"
    HARD_FAIL = "hard_fail"
    NOT_EXECUTABLE_PROMPT_ONLY = "not_executable_prompt_only"
    INVALID_EMBEDDED_OUTPUT = "invalid_embedded_output"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    QUARANTINED = "quarantined"


@dataclass
class AssertionSpec:
    """Deterministic assertion contract for a case."""

    must_contain: list[str] = field(default_factory=list)
    must_not_contain: list[str] = field(default_factory=list)
    json_schema_fields: list[str] = field(default_factory=list)
    exit_code: Optional[int] = None
    file_exists: list[str] = field(default_factory=list)
    exact_output: Optional[str] = None


@dataclass
class RubricDimension:
    """Weighted qualitative/quantitative rubric dimension."""

    dimension: str
    weight: float
    hard_fail_below: Optional[float] = None


@dataclass
class EvalCase:
    """One eval case.

    Suite-authored ``observed_output`` / ``fixture_output`` are golden/expected
    fixtures only. A case is executable only when it declares an ``execute`` block.
    """

    id: str
    input: str = ""
    expected_criteria: list[str] = field(default_factory=list)
    assertions: AssertionSpec = field(default_factory=AssertionSpec)
    golden_output: Optional[str] = None
    suite_authored_output: bool = False
    has_execute: bool = False
    observed_exit_code: Optional[int] = None
    workspace_root: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)
    source_identity: dict[str, Any] = field(default_factory=dict)
    release_identity: dict[str, Any] = field(default_factory=dict)
    declared_effects: list[str] = field(default_factory=list)
    privacy_findings: list[str] = field(default_factory=list)
    compatibility: str = ""

    @property
    def case_id(self) -> str:
        return self.id

    @property
    def is_executable(self) -> bool:
        """True only when the case declares a real execute boundary."""
        return self.has_execute

    # Backward-compat aliases intentionally do NOT treat suite-authored outputs
    # as executable evidence.
    @property
    def observed_output(self) -> Optional[str]:
        return None

    @property
    def fixture_output(self) -> Optional[str]:
        return self.golden_output


@dataclass
class EvalSuite:
    """Loaded eval-suite.yaml representation."""

    skill_id: str
    suite_id: str = ""
    suite_version: str = "0.0.0"
    pass_threshold: float = 0.8
    rubric: list[RubricDimension] = field(default_factory=list)
    cases: list[EvalCase] = field(default_factory=list)
    source_path: Optional[str] = None
    suite_hash: str = ""
    judge_config: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    source_identity: dict[str, Any] = field(default_factory=dict)
    release_identity: dict[str, Any] = field(default_factory=dict)
    declared_effects: list[str] = field(default_factory=list)
    privacy_findings: list[str] = field(default_factory=list)
    compatibility: str = ""
    licence: dict[str, Any] = field(default_factory=dict)
    trust_boundary: str = ""


@dataclass
class AssertionResult:
    """Result of one deterministic assertion check."""

    name: str
    passed: bool
    detail: str = ""
    hard_fail: bool = False


@dataclass
class EvidenceArtifact:
    """Persisted evidence reference for a case or suite run."""

    name: str
    kind: str = "output"
    path: Optional[str] = None
    content_hash: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseResult:
    """Per-case run evidence."""

    case_id: str
    status: CaseStatus
    observed_output: Optional[str] = None
    assertion_results: list[AssertionResult] = field(default_factory=list)
    judge_scores: dict[str, float] = field(default_factory=dict)
    case_score: Optional[float] = None
    evidence: list[EvidenceArtifact] = field(default_factory=list)
    evidence_meta: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    execution_receipt: Optional[dict[str, Any]] = None
    evidence_source: str = "none"

    @property
    def has_observed_evidence(self) -> bool:
        return (
            self.evidence_source == "executor"
            and self.observed_output is not None
            and self.execution_receipt is not None
            and self.status
            not in {
                CaseStatus.NOT_EXECUTABLE_PROMPT_ONLY,
                CaseStatus.INVALID_EMBEDDED_OUTPUT,
            }
        )


@dataclass
class SuiteResult:
    """Aggregated suite run with toolchain and certifiability flags."""

    skill_id: str
    suite_version: str
    suite_hash: str
    case_results: list[CaseResult]
    judge_kind: str
    suite_id: str = ""
    toolchain: dict[str, Any] = field(default_factory=dict)
    weighted_score: Optional[float] = None
    dimension_scores: dict[str, float] = field(default_factory=dict)
    hard_fail_dimensions: list[str] = field(default_factory=list)
    passed: bool = False
    certifiable: bool = False
    reasons: list[str] = field(default_factory=list)
    workspace_receipt: dict[str, Any] = field(default_factory=dict)
    evidence: list[EvidenceArtifact] = field(default_factory=list)
    execution_receipts: list[dict[str, Any]] = field(default_factory=list)
    source_identity: dict[str, Any] = field(default_factory=dict)
    release_identity: dict[str, Any] = field(default_factory=dict)
    declared_effects: list[str] = field(default_factory=list)
    privacy_findings: list[str] = field(default_factory=list)
    compatibility: str = ""
    qualification_outcome: str = ""

    @property
    def has_prompt_only_cases(self) -> bool:
        return any(
            cr.status
            in {
                CaseStatus.NOT_EXECUTABLE_PROMPT_ONLY,
                CaseStatus.INVALID_EMBEDDED_OUTPUT,
            }
            for cr in self.case_results
        )


# Backward-compatible alias used by earlier Phase 3 stubs.
RunResult = SuiteResult
