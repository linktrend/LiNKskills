"""Deterministic runner path with fixture_output / observed_output."""

from __future__ import annotations

from pathlib import Path

from linkskills_eval_runner.certify import certify_run
from linkskills_eval_runner.judge import IndependentDeterministicJudge
from linkskills_eval_runner.models import CaseStatus
from linkskills_eval_runner.runner import load_eval_suite, run_suite
from linkskills_eval_runner.workspace import create_workspace


ROOT = Path(__file__).resolve().parents[2]
CANARY_SUITE = ROOT / "evidence" / "phase3" / "fixtures" / "canary-echo" / "eval-suite.yaml"


def test_canary_suite_with_observed_output_passes_and_certifies():
    assert CANARY_SUITE.is_file(), f"missing canary suite: {CANARY_SUITE}"
    suite = load_eval_suite(CANARY_SUITE)
    assert suite.cases, "canary suite must define cases"
    assert all(c.is_executable for c in suite.cases)

    with create_workspace(fixture_dir=CANARY_SUITE.parent) as ws:
        result = run_suite(
            suite,
            judge=IndependentDeterministicJudge(),
            toolchain={"tools": [{"tool_id": "echo", "version": "1.0.0"}]},
            workspace=ws,
        )
        assert result.passed is True
        assert result.certifiable is True
        assert all(c.status == CaseStatus.PASSED for c in result.case_results)
        decision = certify_run(
            result,
            judge=IndependentDeterministicJudge(),
            rubric=suite.rubric,
            pass_threshold=suite.pass_threshold,
        )
        assert decision.certified is True
        assert decision.profile_hash


def test_fixture_output_failure_is_not_certified(tmp_path: Path):
    suite_path = tmp_path / "eval-suite.yaml"
    suite_path.write_text(
        """
skill_id: fail-echo
suite_id: fail-echo-suite
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
    observed_output: "goodbye"
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
    result = run_suite(suite, judge=IndependentDeterministicJudge())
    assert result.passed is False
    assert any(
        c.status in {CaseStatus.FAILED, CaseStatus.HARD_FAIL}
        for c in result.case_results
    )
    decision = certify_run(result, rubric=suite.rubric, pass_threshold=suite.pass_threshold)
    assert decision.certified is False


def test_fixture_output_file_path_loads(tmp_path: Path):
    fixture = tmp_path / "out.txt"
    fixture.write_text('{"ok": true, "echo": "ping"}\n', encoding="utf-8")
    suite_path = tmp_path / "eval-suite.yaml"
    suite_path.write_text(
        """
skill_id: file-echo
suite_version: 0.0.1
pass_threshold: 0.5
rubric:
  - dimension: correctness
    weight: 1.0
cases:
  - id: from-file
    input: "ping"
    expected_criteria:
      - "ok true"
    fixture_output: out.txt
    assertions:
      must_contain:
        - '"ok": true'
      json_schema_fields:
        - ok
        - echo
""".strip()
        + "\n",
        encoding="utf-8",
    )
    suite = load_eval_suite(suite_path)
    result = run_suite(suite)
    assert result.case_results[0].status == CaseStatus.PASSED
    assert result.passed is True
