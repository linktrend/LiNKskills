"""Critical: prompt-only suites must never certify."""

from __future__ import annotations

from linkskills_eval_runner.certify import certify_run
from linkskills_eval_runner.judge import FakeJudge, PromptOnlyJudge, judge_is_rejected
from linkskills_eval_runner.models import (
    CaseResult,
    CaseStatus,
    EvalCase,
    EvalSuite,
    RubricDimension,
)
from linkskills_eval_runner.runner import run_suite


def test_prompt_only_judge_is_rejected_by_certifier():
    assert judge_is_rejected(PromptOnlyJudge())
    assert judge_is_rejected(FakeJudge())

    suite = EvalSuite(
        skill_id="canary-echo",
        suite_version="0.0.1",
        pass_threshold=0.5,
        rubric=[RubricDimension(dimension="correctness", weight=1.0)],
        cases=[
            EvalCase(
                id="legacy-prompt",
                input="Say hello",
                expected_criteria=["mentions hello"],
                # no observed_output / fixture_output
            )
        ],
    )
    result = run_suite(suite, judge=PromptOnlyJudge())
    assert result.has_prompt_only_cases
    assert any(
        c.status == CaseStatus.NOT_EXECUTABLE_PROMPT_ONLY for c in result.case_results
    )
    decision = certify_run(result, judge=PromptOnlyJudge(), rubric=suite.rubric)
    assert decision.certified is False
    assert "not_executable_prompt_only" in decision.reason or "prompt" in decision.reason


def test_prompt_only_case_blocks_certification_even_with_independent_judge():
    suite = EvalSuite(
        skill_id="canary-echo",
        suite_version="0.0.1",
        pass_threshold=0.1,
        rubric=[RubricDimension(dimension="correctness", weight=1.0)],
        cases=[
            EvalCase(id="no-output", input="prompt only scenario", expected_criteria=["x"]),
        ],
    )
    result = run_suite(suite)
    decision = certify_run(result, rubric=suite.rubric, pass_threshold=0.1)
    assert decision.certified is False
    assert "not_executable_prompt_only" in decision.reason


def test_fake_judge_kind_cannot_certify_even_with_observed_output():
    case = CaseResult(
        case_id="c1",
        status=CaseStatus.PASSED,
        observed_output="hello world",
        judge_scores={"correctness": 1.0},
        evidence_meta={"executable": True},
    )
    from linkskills_eval_runner.models import SuiteResult

    run = SuiteResult(
        skill_id="canary-echo",
        suite_version="0.0.1",
        suite_hash="abc",
        case_results=[case],
        judge_kind="fake",
        weighted_score=1.0,
        passed=True,
        certifiable=True,
    )
    decision = certify_run(run, judge=FakeJudge())
    assert decision.certified is False
    assert "fake" in decision.reason
