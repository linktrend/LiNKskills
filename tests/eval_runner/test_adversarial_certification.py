"""Adversarial certification tests — suites must not self-certify by embedding answers."""

from __future__ import annotations

from pathlib import Path

from linkskills_eval_runner.certify import certify_run
from linkskills_eval_runner.judge import IndependentDeterministicJudge
from linkskills_eval_runner.models import CaseResult, CaseStatus, SuiteResult
from linkskills_eval_runner.runner import load_eval_suite, run_suite


ROOT = Path(__file__).resolve().parents[2]


def test_fixture_output_alone_cannot_certify(tmp_path: Path):
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
""".strip()
        + "\n",
        encoding="utf-8",
    )
    suite = load_eval_suite(suite_path)
    result = run_suite(suite, repo_root=ROOT)
    assert result.case_results[0].status == CaseStatus.INVALID_EMBEDDED_OUTPUT
    decision = certify_run(result, rubric=suite.rubric, pass_threshold=0.5)
    assert decision.certified is False


def test_fabricated_artifact_metadata_cannot_certify():
    """A hand-built SuiteResult with fake evidence_meta must not certify."""
    fabricated = CaseResult(
        case_id="fabricated",
        status=CaseStatus.PASSED,
        observed_output="HELLO_CANARY",
        judge_scores={"correctness": 1.0},
        case_score=1.0,
        evidence_meta={
            "executable": True,
            "evidence_source": "suite_authored",
            "output_sha256": "0" * 64,
            "fabricated": True,
        },
        evidence_source="suite_authored",
        execution_receipt={
            "receipt_hash": "deadbeef",
            "case_id": "fabricated",
            "skill_id": "x",
            "suite_hash": "y",
            "skill_release_hash": "z",
            "execution_profile_hash": "p",
            "stdout_hash": "s",
            "stderr_hash": "e",
            "tool_calls": [],
            "environment": {},
            "evidence_source": "suite_authored",
            "executor_version": "forged",
            "receipt_id": "r1",
        },
    )
    run = SuiteResult(
        skill_id="fabricated-skill",
        suite_version="0.0.1",
        suite_hash="suitehash",
        case_results=[fabricated],
        judge_kind="independent_deterministic",
        suite_id="fabricated-suite",
        weighted_score=1.0,
        passed=True,
        certifiable=True,
        execution_receipts=[fabricated.execution_receipt or {}],
    )
    decision = certify_run(
        run,
        judge=IndependentDeterministicJudge(),
        pass_threshold=0.1,
    )
    assert decision.certified is False


def test_tampered_receipt_hash_cannot_certify(tmp_path: Path):
    suite_path = tmp_path / "eval-suite.yaml"
    suite_path.write_text(
        """
skill_id: tamper
suite_version: 0.0.1
pass_threshold: 0.1
rubric:
  - dimension: correctness
    weight: 1.0
cases:
  - id: ok
    execute:
      kind: command
      argv: ["python3", "-c", "print('ok')"]
    assertions:
      must_contain: ["ok"]
      exit_code: 0
""".strip()
        + "\n",
        encoding="utf-8",
    )
    suite = load_eval_suite(suite_path)
    result = run_suite(suite, repo_root=ROOT)
    assert result.passed is True
    # Tamper with the sealed receipt hash.
    result.case_results[0].execution_receipt["receipt_hash"] = "0" * 64
    decision = certify_run(result, rubric=suite.rubric, pass_threshold=0.1)
    assert decision.certified is False
    assert "receipt" in decision.reason.lower()
