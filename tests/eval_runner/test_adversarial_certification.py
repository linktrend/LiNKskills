"""Adversarial certification tests — suites must not self-certify by embedding answers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from linkskills_eval_runner.certify import certify_run
from linkskills_eval_runner.executor import (
    UNSET_SKILL_RELEASE_HASH,
    compute_skill_release_hash,
)
from linkskills_eval_runner.judge import IndependentDeterministicJudge
from linkskills_eval_runner.models import CaseResult, CaseStatus, SuiteResult
from linkskills_eval_runner.runner import load_eval_suite, run_suite
from linkskills_eval_runner.workspace import create_workspace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from isolation_probe import proven_executor_isolation_available  # noqa: E402

SKILL_RELEASE = ROOT / "evidence/phase3/fixtures/canary-echo/skill-release"
CANARY_SUITE = ROOT / "evidence/phase3/fixtures/canary-echo/eval-suite.yaml"


def _canary_toolchain() -> dict:
    """Exact toolchain hashes for canary (ADR 0006)."""
    sys.path.insert(0, str(ROOT / "packages" / "tool_runtime"))
    from linkskills_tool_runtime.resolve import resolve_tool

    resolved = resolve_tool(
        ROOT / "tools" / "text-echo",
        tool_id="text-echo",
        version="1.0.0",
    )
    source_hash = resolved.descriptor.source_hash
    tool_hash = resolved.bundle_hash or source_hash
    return {
        "tools": [
            {
                "tool_id": resolved.tool_id,
                "version": resolved.version,
                "source_hash": source_hash,
                "tool_hash": tool_hash,
            }
        ]
    }


CANARY_TOOLCHAIN = _canary_toolchain()


def _simple_command_suite(tmp_path: Path) -> Path:
    suite_path = tmp_path / "eval-suite.yaml"
    suite_path.write_text(
        """
skill_id: adversarial-cmd
suite_id: adversarial-cmd-suite
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
    return suite_path


def _temp_skill_release(tmp_path: Path, *, marker: str) -> Path:
    skill_dir = tmp_path / f"skill-release-{marker}"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        f"# adversarial release {marker}\n\nmarker: {marker}\n",
        encoding="utf-8",
    )
    return skill_dir


def test_unset_skill_release_cannot_certify(tmp_path: Path):
    """Running without skill_dir / release hash yields skill-release:unset — no certify."""
    suite = load_eval_suite(_simple_command_suite(tmp_path))
    result = run_suite(suite, repo_root=ROOT)
    assert result.passed is True
    assert all(
        (c.execution_receipt or {}).get("skill_release_hash") == UNSET_SKILL_RELEASE_HASH
        for c in result.case_results
    )
    decision = certify_run(result, rubric=suite.rubric, pass_threshold=0.1)
    assert decision.certified is False
    assert "unset" in decision.reason.lower()
    assert "skill-release" in decision.reason.lower()


def test_mismatched_release_hash_cannot_certify(tmp_path: Path):
    """Run with skill_dir A, then certify against expected hash B — refuse."""
    if not proven_executor_isolation_available():
        pytest.skip(
            "host cannot prove FS/network isolation; sealed receipts unavailable "
            "(macOS allowlist typically unproven — see ADR 0009)"
        )

    skill_a = _temp_skill_release(tmp_path, marker="A")
    skill_b = _temp_skill_release(tmp_path, marker="B")
    hash_a = compute_skill_release_hash(skill_a)
    hash_b = compute_skill_release_hash(skill_b)
    assert hash_a != hash_b
    assert not hash_a.endswith(":unset")

    suite = load_eval_suite(_simple_command_suite(tmp_path))
    result = run_suite(suite, repo_root=ROOT, skill_dir=skill_a)
    assert result.passed is True
    assert all(
        (c.execution_receipt or {}).get("skill_release_hash") == hash_a
        for c in result.case_results
    )

    decision = certify_run(
        result,
        rubric=suite.rubric,
        pass_threshold=0.1,
        expected_skill_release_hash=hash_b,
    )
    assert decision.certified is False
    assert "mismatch" in decision.reason.lower()
    assert decision.skill_release_hash == hash_a


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


def test_externally_fabricated_executor_receipt_cannot_certify(tmp_path: Path):
    """Forged receipt claiming evidence_source=executor still fails seal check."""
    skill_dir = _temp_skill_release(tmp_path, marker="forge")
    release_hash = compute_skill_release_hash(skill_dir)
    forged = CaseResult(
        case_id="forged",
        status=CaseStatus.PASSED,
        observed_output="ok",
        judge_scores={"correctness": 1.0},
        case_score=1.0,
        evidence_meta={"executable": True, "evidence_source": "executor"},
        evidence_source="executor",
        execution_receipt={
            "receipt_id": "forged-receipt",
            "receipt_hash": "0" * 64,
            "case_id": "forged",
            "skill_id": "forged-skill",
            "suite_id": "forged-suite",
            "suite_hash": "suitehash",
            "skill_release_hash": release_hash,
            "execution_profile_hash": "profilehash",
            "stdout_hash": "a" * 64,
            "stderr_hash": "b" * 64,
            "tool_calls": [],
            "environment": {},
            "toolchain": {},
            "evidence_source": "executor",
            "executor_version": "forged",
            "exit_code": 0,
            "artifact_hashes": [],
            "started_at": "2026-01-01T00:00:00Z",
            "finished_at": "2026-01-01T00:00:01Z",
        },
    )
    run = SuiteResult(
        skill_id="forged-skill",
        suite_version="0.0.1",
        suite_hash="suitehash",
        case_results=[forged],
        judge_kind="independent_deterministic",
        suite_id="forged-suite",
        weighted_score=1.0,
        passed=True,
        certifiable=True,
        execution_receipts=[forged.execution_receipt or {}],
    )
    decision = certify_run(
        run,
        judge=IndependentDeterministicJudge(),
        pass_threshold=0.1,
        expected_skill_release_hash=release_hash,
    )
    assert decision.certified is False
    assert "receipt" in decision.reason.lower()


def test_tampered_receipt_hash_cannot_certify(tmp_path: Path):
    skill_dir = _temp_skill_release(tmp_path, marker="tamper")
    suite = load_eval_suite(_simple_command_suite(tmp_path))
    result = run_suite(suite, repo_root=ROOT, skill_dir=skill_dir)
    assert result.passed is True
    # Tamper with the sealed receipt hash.
    result.case_results[0].execution_receipt["receipt_hash"] = "0" * 64
    decision = certify_run(
        result,
        rubric=suite.rubric,
        pass_threshold=0.1,
        expected_skill_release_hash=compute_skill_release_hash(skill_dir),
    )
    assert decision.certified is False
    assert "receipt" in decision.reason.lower()


def test_repeated_clean_runs_preserve_profile_identity():
    """Clean reruns keep suite/release/profile hashes; receipt_hashes may differ."""
    if not proven_executor_isolation_available():
        pytest.skip(
            "host cannot prove FS/network isolation; cannot mint certifiable receipts"
        )

    assert CANARY_SUITE.is_file(), f"missing canary suite: {CANARY_SUITE}"
    assert SKILL_RELEASE.is_dir(), f"missing skill release: {SKILL_RELEASE}"
    suite = load_eval_suite(CANARY_SUITE)
    release_hash = compute_skill_release_hash(SKILL_RELEASE)
    assert release_hash != UNSET_SKILL_RELEASE_HASH

    runs = []
    for _ in range(2):
        with create_workspace(fixture_dir=CANARY_SUITE.parent) as ws:
            result = run_suite(
                suite,
                judge=IndependentDeterministicJudge(),
                toolchain=CANARY_TOOLCHAIN,
                workspace=ws,
                repo_root=ROOT,
                skill_dir=SKILL_RELEASE,
            )
            decision = certify_run(
                result,
                judge=IndependentDeterministicJudge(),
                rubric=suite.rubric,
                pass_threshold=suite.pass_threshold,
                expected_skill_release_hash=release_hash,
            )
            assert result.passed is True, result.reasons
            assert decision.certified is True, decision.reason
            runs.append((result, decision))

    (result_a, decision_a), (result_b, decision_b) = runs
    assert result_a.suite_hash == result_b.suite_hash == suite.suite_hash
    assert decision_a.skill_release_hash == decision_b.skill_release_hash == release_hash
    assert decision_a.profile_hash == decision_b.profile_hash
    assert decision_a.profile_hash

    profile_a = {
        (c.execution_receipt or {}).get("execution_profile_hash")
        for c in result_a.case_results
    }
    profile_b = {
        (c.execution_receipt or {}).get("execution_profile_hash")
        for c in result_b.case_results
    }
    assert profile_a == profile_b == {decision_a.profile_hash}

    # Receipts include timestamps/ids — hashes may differ across clean runs.
    assert decision_a.receipt_hashes
    assert decision_b.receipt_hashes
    assert len(decision_a.receipt_hashes) == len(decision_b.receipt_hashes)
