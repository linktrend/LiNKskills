"""Deterministic runner path with real packaged-tool execution."""

from __future__ import annotations

from pathlib import Path

from linkskills_eval_runner.certify import certify_run
from linkskills_eval_runner.judge import IndependentDeterministicJudge
from linkskills_eval_runner.models import CaseStatus
from linkskills_eval_runner.runner import load_eval_suite, run_suite
from linkskills_eval_runner.workspace import create_workspace


ROOT = Path(__file__).resolve().parents[2]
CANARY_SUITE = ROOT / "evidence" / "phase3" / "fixtures" / "canary-echo" / "eval-suite.yaml"


def test_canary_suite_executes_and_certifies():
    assert CANARY_SUITE.is_file(), f"missing canary suite: {CANARY_SUITE}"
    suite = load_eval_suite(CANARY_SUITE)
    assert suite.cases, "canary suite must define cases"
    assert all(c.is_executable for c in suite.cases)
    assert all(not c.suite_authored_output for c in suite.cases)

    with create_workspace(fixture_dir=CANARY_SUITE.parent) as ws:
        result = run_suite(
            suite,
            judge=IndependentDeterministicJudge(),
            toolchain={"tools": [{"tool_id": "text-echo", "version": "1.0.0"}]},
            workspace=ws,
            repo_root=ROOT,
        )
        assert result.passed is True, result.reasons
        assert result.certifiable is True
        assert all(c.status == CaseStatus.PASSED for c in result.case_results)
        assert all(c.evidence_source == "executor" for c in result.case_results)
        assert all(c.execution_receipt for c in result.case_results)
        decision = certify_run(
            result,
            judge=IndependentDeterministicJudge(),
            rubric=suite.rubric,
            pass_threshold=suite.pass_threshold,
        )
        assert decision.certified is True, decision.reason
        assert decision.profile_hash
        assert decision.receipt_hashes


def test_suite_authored_observed_output_cannot_certify(tmp_path: Path):
    suite_path = tmp_path / "eval-suite.yaml"
    suite_path.write_text(
        """
skill_id: embedded-cheat
suite_id: embedded-cheat-suite
suite_version: 0.0.1
pass_threshold: 0.1
rubric:
  - dimension: correctness
    weight: 1.0
cases:
  - id: cheat
    input: "echo hello"
    expected_criteria:
      - "contains hello"
    observed_output: "hello"
    assertions:
      must_contain:
        - "hello"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    suite = load_eval_suite(suite_path)
    result = run_suite(suite, judge=IndependentDeterministicJudge(), repo_root=ROOT)
    assert result.passed is False
    assert result.case_results[0].status == CaseStatus.INVALID_EMBEDDED_OUTPUT
    decision = certify_run(result, rubric=suite.rubric, pass_threshold=suite.pass_threshold)
    assert decision.certified is False


def test_command_execute_failure_is_not_certified(tmp_path: Path):
    suite_path = tmp_path / "eval-suite.yaml"
    suite_path.write_text(
        """
skill_id: fail-cmd
suite_id: fail-cmd-suite
suite_version: 0.0.1
pass_threshold: 0.8
rubric:
  - dimension: correctness
    weight: 1.0
    hard_fail_below: 0.5
cases:
  - id: bad-output
    input: "echo hello"
    expected_criteria:
      - "contains hello"
    execute:
      kind: command
      argv: ["python3", "-c", "print('goodbye')"]
    assertions:
      must_contain:
        - "hello"
      must_not_contain:
        - "goodbye"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    suite = load_eval_suite(suite_path)
    result = run_suite(suite, judge=IndependentDeterministicJudge(), repo_root=ROOT)
    assert result.passed is False
    assert any(
        c.status in {CaseStatus.FAILED, CaseStatus.HARD_FAIL}
        for c in result.case_results
    )
    decision = certify_run(result, rubric=suite.rubric, pass_threshold=suite.pass_threshold)
    assert decision.certified is False
