"""ED-03 executed-case qualification: confined consumer-profile drivers."""

from __future__ import annotations

from pathlib import Path

from linkskills_eval_runner.certify import certify_run
from linkskills_eval_runner.consumer_profiles import CURSOR_MACOS, resolve_driver
from linkskills_eval_runner.ed03 import (
    INITIAL_RELEASE_PROFILES,
    classify_combination,
    classify_case_families,
    case_records,
    qualify_initial_release_profiles,
)
from linkskills_eval_runner.judge import IndependentDeterministicJudge
from linkskills_eval_runner.runner import load_eval_suite, run_suite

ROOT = Path(__file__).resolve().parents[2]


def test_five_combinations_are_frozen() -> None:
    assert len(INITIAL_RELEASE_PROFILES) == 5
    assert {row["skillId"] for row in INITIAL_RELEASE_PROFILES} == {
        "git-safeguard",
        "persistent-qa",
        "repository-manager",
        "skill-template",
        "tool-architect",
    }
    assert {row["runtimeProfile"] for row in INITIAL_RELEASE_PROFILES} == {CURSOR_MACOS}


def test_yaml_suites_have_all_families_and_execute_blocks() -> None:
    for row in INITIAL_RELEASE_PROFILES:
        skill_dir = ROOT / "skills" / row["skillId"]
        cases = case_records(skill_dir)
        families = classify_case_families(cases)
        assert all(families[name] for name in families), (row["skillId"], families)
        executable = [case["id"] for case in cases if case["hasExecute"]]
        assert executable, row["skillId"]
        suite = load_eval_suite(skill_dir / "references" / "eval-suite.yaml")
        assert all(case.has_execute for case in suite.cases), row["skillId"]
        assert all(case.raw["execute"]["kind"] == "consumer_profile" for case in suite.cases)


def test_fake_or_prompt_evidence_is_quarantined() -> None:
    row = classify_combination(
        skill_id="git-safeguard",
        version="1.1.0",
        runtime_profile=CURSOR_MACOS,
        source_version="1.1.0",
        compatible_profiles=[CURSOR_MACOS],
        families={name: ["c"] for name in ("success", "guardrail", "failure", "recovery", "privacy")},
        executable_case_ids=["c"],
        evidence_kind="prompt_only",
        certified=True,
        sealed_receipts=True,
    )
    assert row["lifecycle"] == "quarantined"


def test_certified_without_execute_is_quarantined() -> None:
    row = classify_combination(
        skill_id="git-safeguard",
        version="1.1.0",
        runtime_profile=CURSOR_MACOS,
        source_version="1.1.0",
        compatible_profiles=[CURSOR_MACOS],
        families={name: ["c"] for name in ("success", "guardrail", "failure", "recovery", "privacy")},
        executable_case_ids=[],
        certified=True,
        sealed_receipts=True,
    )
    assert row["lifecycle"] == "quarantined"
    assert row["reason"] == "certified_without_executed_cases"


def test_missing_owner_receipt_stays_eval_pending() -> None:
    row = classify_combination(
        skill_id="git-safeguard",
        version="1.1.0",
        runtime_profile=CURSOR_MACOS,
        source_version="1.1.0",
        compatible_profiles=[CURSOR_MACOS],
        families={name: ["c"] for name in ("success", "guardrail", "failure", "recovery", "privacy")},
        executable_case_ids=["c"],
        certified=True,
        sealed_receipts=True,
        missing_owner_receipts=[{"requiredKind": "cursor-project-scoped-owner-live-receipt"}],
    )
    assert row["lifecycle"] == "eval_pending"
    assert "missing_owner_receipt" in row["reason"]


def test_cursor_driver_names_exact_missing_live_owner_receipt() -> None:
    binding = resolve_driver(CURSOR_MACOS).binding(ROOT)
    kinds = {item["requiredKind"] for item in binding["missingOwnerReceipts"]}
    assert "cursor-project-scoped-owner-live-receipt" not in kinds
    assert binding["pendingConsumerReceipts"][0]["requiredKind"] == "cursor-project-scoped-owner-live-receipt"
    assert "xp-02-cursor-owner-live-receipt" not in kinds
    assert "eval-runner-issuer-secretref" in kinds
    assert binding["ownerReceipt"]["requiredKind"] == "cursor-project-scoped-owner-live-receipt"
    assert binding["liveConsumerActor"] is False
    assert binding["guiLaunch"] is False


def test_xp02_owner_receipt_required_only_when_shared_global_declared(monkeypatch) -> None:
    from linkskills_eval_runner.consumer_profiles import inspect_xp02_cursor_receipt

    default = resolve_driver(CURSOR_MACOS).binding(ROOT)
    assert all(item.get("requiredKind") != "xp-02-cursor-owner-live-receipt" for item in default["missingOwnerReceipts"])
    xp02 = inspect_xp02_cursor_receipt(ROOT)
    assert xp02["required"] is False
    assert xp02["live"] is False
    assert xp02["reason"] == "xp02_not_required_project_scoped_default"

    monkeypatch.setenv("LINKSKILLS_CURSOR_SHARED_GLOBAL_MUTATION", "declared")
    declared = resolve_driver(CURSOR_MACOS).binding(ROOT)
    kinds = {item["requiredKind"] for item in declared["pendingConsumerReceipts"]}
    assert "cursor-project-scoped-owner-live-receipt" in kinds
    assert "xp-02-cursor-owner-live-receipt" in kinds


def test_process_issuer_key_without_secretref_authority_is_not_live(monkeypatch) -> None:
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", "observation-only")
    monkeypatch.delenv("LINKSKILLS_EVAL_RUNNER_ISSUER_AUTHORITY", raising=False)
    from linkskills_eval_runner.consumer_profiles import inspect_issuer_receipt

    row = inspect_issuer_receipt()
    assert row["present"] is True
    assert row["live"] is False
    assert row["reason"] == "weak_process_issuer_material"
    assert "observation-only" not in str(row)


def test_weak_process_issuer_material_is_rejected_without_logging_value(monkeypatch) -> None:
    from linkskills_eval_runner.consumer_profiles import inspect_issuer_receipt

    weak = "short-issuer-material"
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", weak)
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_AUTHORITY", "secretref")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_ID", "eval-runner-operator")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_SECRET_REF", "LINKTREND_SKILLS_DEV_EVAL_ISSUER_KEY")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_SECRET_VERSION", "3")
    row = inspect_issuer_receipt()
    assert row["live"] is False
    assert row["reason"] == "weak_process_issuer_material"
    dumped = str(row)
    assert weak not in dumped
    assert "short-issuer" not in dumped


def test_authority_label_or_latest_version_cannot_make_issuer_live(monkeypatch) -> None:
    from linkskills_eval_runner.consumer_profiles import inspect_issuer_receipt

    monkeypatch.delenv("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", raising=False)
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_AUTHORITY", "secretref")
    monkeypatch.delenv("LINKSKILLS_EVAL_RUNNER_ISSUER_ID", raising=False)
    monkeypatch.delenv("LINKSKILLS_EVAL_RUNNER_ISSUER_SECRET_REF", raising=False)
    monkeypatch.delenv("LINKSKILLS_EVAL_RUNNER_ISSUER_SECRET_VERSION", raising=False)
    label_only = inspect_issuer_receipt()
    assert label_only["live"] is False
    assert label_only["reason"] == "authority_label_insufficient"

    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_ID", "eval-runner-operator")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_SECRET_REF", "LINKTREND_SKILLS_DEV_EVAL_ISSUER_KEY")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_SECRET_VERSION", "latest")
    latest = inspect_issuer_receipt()
    assert latest["live"] is False
    assert latest["reason"] == "mutable_secret_version_rejected"
    assert latest["secretVersionImmutable"] is False


def test_issuer_live_requires_immutable_secretref_version_and_identity(monkeypatch) -> None:
    from linkskills_eval_runner.consumer_profiles import inspect_issuer_receipt

    monkeypatch.delenv("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", raising=False)
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_AUTHORITY", "secretref")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_ID", "eval-runner-operator")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_SECRET_REF", "LINKTREND_SKILLS_DEV_EVAL_ISSUER_KEY")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_SECRET_VERSION", "7")
    row = inspect_issuer_receipt()
    assert row["live"] is True
    assert row["reason"] is None
    assert row["secretRefPresent"] is True
    assert row["secretVersionImmutable"] is True
    assert row["issuerIdentityPresent"] is True
    assert "LINKTREND_SKILLS_DEV_EVAL_ISSUER_KEY" not in str(row.values())


def test_git_safeguard_confined_consumer_profile_executes(monkeypatch) -> None:
    monkeypatch.setenv("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "allow_unproven")
    monkeypatch.setenv("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", "test-issuer-key")
    skill_dir = ROOT / "skills" / "git-safeguard"
    suite = load_eval_suite(skill_dir / "references" / "eval-suite.yaml")
    toolchain = resolve_driver(CURSOR_MACOS).toolchain(ROOT)
    result = run_suite(
        suite,
        judge=IndependentDeterministicJudge(),
        toolchain=toolchain,
        repo_root=ROOT,
        skill_dir=skill_dir,
    )
    assert result.passed, result.reasons
    assert all(case.evidence_source == "executor" for case in result.case_results)
    assert all(case.execution_receipt for case in result.case_results)
    decision = certify_run(result, rubric=suite.rubric)
    # Isolation is unproven in this unit path; certification must stay closed.
    if any(
        (case.execution_receipt or {}).get("network_isolation") != "denied"
        for case in result.case_results
    ):
        assert decision.certified is False


def test_source_only_matrix_never_claims_usable() -> None:
    matrix = qualify_initial_release_profiles(ROOT, execute=False)
    assert matrix["complete"] is True
    assert matrix["usable"] == []
    assert len(matrix["evalPending"]) == 5
    assert matrix["quarantined"] == []
    assert matrix["cursorOwnerReceipt"]["requiredKind"] == "cursor-project-scoped-owner-live-receipt"
    assert matrix["cursorXp02Receipt"]["required"] is False
    assert all(row["lifecycle"] == "eval_pending" for row in matrix["combinations"])
