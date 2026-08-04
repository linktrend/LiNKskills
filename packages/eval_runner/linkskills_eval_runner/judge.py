"""Independent judge adapters for qualitative rubric dimensions.

Certification rejects FakeJudge and PromptOnlyJudge. Only independent judges
that operate on observed outputs may participate in certifiable runs.
"""

from __future__ import annotations

import re
from typing import Any, Optional, Protocol, runtime_checkable

from .models import AssertionResult, EvalCase, RubricDimension


def _tokenize(text: str) -> set[str]:
    return {tok for tok in re.findall(r"[a-z0-9_./:-]+", text.lower()) if tok}


def _keyword_overlap_score(criteria: list[str], observed_output: Optional[str]) -> float:
    """Score in [0, 1] from keyword overlap between criteria and observed output."""
    if not criteria:
        return 0.0
    if observed_output is None:
        return 0.0
    observed_tokens = _tokenize(observed_output)
    if not observed_tokens:
        return 0.0
    per_criterion: list[float] = []
    for item in criteria:
        tokens = _tokenize(item)
        if not tokens:
            per_criterion.append(0.0)
            continue
        hits = sum(1 for tok in tokens if tok in observed_tokens)
        per_criterion.append(hits / len(tokens))
    return sum(per_criterion) / len(per_criterion)


@runtime_checkable
class QualitativeJudge(Protocol):
    """Judge interface consumed by the runner and certifier."""

    kind: str

    def score(
        self,
        case: EvalCase,
        observed_output: Optional[str],
        rubric: list[RubricDimension],
        assertion_results: list[AssertionResult],
    ) -> dict[str, float]:
        """Return per-dimension scores in [0.0, 1.0]."""


# Backward-compatible Protocol alias.
Judge = QualitativeJudge


class FakeJudge:
    """Deterministic test double scoring via expected_criteria keyword overlap.

    Explicitly rejected by the certifier — never use for certification.
    """

    kind = "fake"

    def score(
        self,
        case: EvalCase,
        observed_output: Optional[str],
        rubric: list[RubricDimension],
        assertion_results: list[AssertionResult],
    ) -> dict[str, float]:
        _ = assertion_results
        overlap = _keyword_overlap_score(case.expected_criteria, observed_output)
        if not rubric:
            return {"overlap": overlap}
        return {dim.dimension: overlap for dim in rubric}


class PromptOnlyJudge:
    """Legacy judge that scores from prompt/criteria alone without observed output.

    Explicitly rejected by the certifier — cannot certify.
    """

    kind = "prompt_only"

    def score(
        self,
        case: EvalCase,
        observed_output: Optional[str],
        rubric: list[RubricDimension],
        assertion_results: list[AssertionResult],
    ) -> dict[str, float]:
        # Deliberately ignores observed_output; scores from criteria presence only.
        _ = observed_output, assertion_results
        if not case.expected_criteria:
            return {dim.dimension: 0.0 for dim in rubric} if rubric else {"prompt": 0.0}
        score = 0.9
        if not rubric:
            return {"prompt": score}
        return {dim.dimension: score for dim in rubric}


class IndependentDeterministicJudge:
    """Independent judge that derives dimension scores from assertion evidence only.

    Suitable for Phase 3 canary/deterministic suites. Does not invent scores from
    identifiers or rubric names alone.
    """

    kind = "independent_deterministic"

    def score(
        self,
        case: EvalCase,
        observed_output: Optional[str],
        rubric: list[RubricDimension],
        assertion_results: list[AssertionResult],
    ) -> dict[str, float]:
        _ = case
        if observed_output is None:
            return {dim.dimension: 0.0 for dim in rubric} if rubric else {"score": 0.0}
        if not assertion_results:
            # Observed evidence present but no assertions: partial credit only.
            base = 0.5
            return {dim.dimension: base for dim in rubric} if rubric else {"score": base}
        passed = sum(1 for r in assertion_results if r.passed)
        ratio = passed / len(assertion_results)
        return {dim.dimension: ratio for dim in rubric} if rubric else {"score": ratio}


# Judge kinds the certifier must reject.
CERTIFIER_REJECTED_JUDGE_KINDS = frozenset({"fake", "prompt_only"})
CERTIFIER_REJECTED_JUDGE_TYPES = (FakeJudge, PromptOnlyJudge)


def judge_is_rejected(judge: Any) -> bool:
    """Return True when *judge* is forbidden for certification."""
    if isinstance(judge, CERTIFIER_REJECTED_JUDGE_TYPES):
        return True
    kind = getattr(judge, "kind", None)
    return kind in CERTIFIER_REJECTED_JUDGE_KINDS
