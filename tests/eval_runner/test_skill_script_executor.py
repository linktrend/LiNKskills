"""Confined execution coverage for scripts bundled with a skill release."""

from __future__ import annotations

import json
from pathlib import Path

from linkskills_eval_runner.executor import execute_case
from linkskills_eval_runner.judge import IndependentDeterministicJudge
from linkskills_eval_runner.runner import load_eval_suite, run_suite
from linkskills_eval_runner.workspace import EvalWorkspace


def _write_skill(tmp_path: Path) -> tuple[Path, Path]:
    skill = tmp_path / "sample-skill"
    script = skill / "scripts" / "route.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "import json, sys\n"
        "print(json.dumps({'status': 'SELECTED', 'selected_route': sys.argv[1]}))\n",
        encoding="utf-8",
    )
    suite_path = skill / "references" / "eval-suite.yaml"
    suite_path.parent.mkdir(parents=True)
    suite_path.write_text(
        """schema_version: "0.1"
suite_id: sample-skill-suite
skill_id: sample-skill
suite_version: 1.0.0
pass_threshold: 1.0
rubric:
  - dimension: correctness
    weight: 1.0
    hard_fail_below: 1.0
scenarios:
  - id: route
    input: chosen-route
    execute:
      kind: skill_script
      script: scripts/route.py
      append_input_argv: true
    assertions:
      must_contain: ['"status": "SELECTED"', '"selected_route": "chosen-route"']
      json_schema_fields: [status, selected_route]
      exit_code: 0
""",
        encoding="utf-8",
    )
    return skill, suite_path


def test_skill_script_executes_from_staged_release(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "allow_unproven")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", "test-issuer-key")
    skill, suite_path = _write_skill(tmp_path)
    suite = load_eval_suite(suite_path)

    result = run_suite(
        suite,
        judge=IndependentDeterministicJudge(),
        skill_dir=skill,
        skill_release_hash="a" * 64,
    )

    assert result.passed
    case = result.case_results[0]
    assert json.loads(case.observed_output or "{}")["selected_route"] == "chosen-route"
    call = (case.execution_receipt or {})["tool_calls"][0]
    assert call["adapter_kind"] == "confined_skill_script"
    assert len(call["tool_hash"]) == 64
    assert call["argv"] == ["python", "skill/scripts/route.py", "chosen-route"]


def test_skill_script_rejects_path_escape(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "allow_unproven")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", "test-issuer-key")
    skill, suite_path = _write_skill(tmp_path)
    suite = load_eval_suite(suite_path)
    case = suite.cases[0]
    case.raw["execute"]["script"] = "../outside.py"

    with EvalWorkspace() as workspace:
        capture = execute_case(
            case,
            suite=suite,
            workspace=workspace,
            skill_dir=skill,
            skill_release_hash="b" * 64,
        )

    assert not capture.ok
    assert capture.receipt is None
    assert "safe relative script path" in (capture.error or "")


def test_skill_script_rejects_symlink_anywhere_in_release(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "allow_unproven")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", "test-issuer-key")
    skill, suite_path = _write_skill(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("must not be staged", encoding="utf-8")
    (skill / "unsafe-link").symlink_to(outside)
    suite = load_eval_suite(suite_path)

    with EvalWorkspace() as workspace:
        capture = execute_case(
            suite.cases[0],
            suite=suite,
            workspace=workspace,
            skill_dir=skill,
            skill_release_hash="c" * 64,
        )

    assert not capture.ok
    assert capture.receipt is None
    assert "containing symlinks" in (capture.error or "")


def test_hybrid_routing_suite_is_executable_and_complete() -> None:
    root = Path(__file__).resolve().parents[2]
    suite = load_eval_suite(
        root / "skills" / "hybrid-development-methods" / "references" / "eval-suite.yaml"
    )

    assert len(suite.cases) == 22
    assert all(case.has_execute for case in suite.cases)
    assert all(case.raw["execute"]["kind"] == "skill_script" for case in suite.cases)
    assert len([case for case in suite.cases if case.id.startswith("route-")]) == 19
    assert {case.id for case in suite.cases if not case.id.startswith("route-")} == {
        "ambiguous-overlap",
        "consumer-boundary",
        "no-match",
    }
