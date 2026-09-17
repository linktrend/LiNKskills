"""Focused regression for identity-bound release-gate evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.gitops.promotion_receipt_gate import evaluate_release_path
from scripts.gitops.release_gate import (
    EVIDENCE_KIND,
    ReleaseGateError,
    evidence_from_inventory,
    verify_release_evidence,
)
from scripts.gitops.run_delivery_profile import (
    DeliveryProfileError,
    classify_risk,
    identity_digest,
    load_profile,
    run_profile,
)


def _identity(**overrides: str) -> dict[str, str]:
    payload = {
        "repository": "linktrend/LiNKskills",
        "headCommit": "a" * 40,
        "gitTree": "b" * 40,
        "dependencyDigest": "sha256:" + ("1" * 64),
        "profileDigest": "sha256:" + ("2" * 64),
        "workflowDigest": "sha256:" + ("3" * 64),
    }
    payload.update(overrides)
    return payload


def _inventory(*, ok: bool = True, identity: dict[str, str] | None = None, commands: list | None = None) -> dict:
    identity = identity or _identity()
    commands = commands or [["python3", "scripts/gitops/secret_scan.py"]]
    rows = [{"id": "release-001", "argv": commands[0], "boundary": "release", "status": "passed" if ok else "failed"}]
    inventory = {
        "profile": "release",
        "boundary": "release",
        "ok": ok,
        "complete": True,
        "workspaceMutated": False,
        "identity": identity,
        "identityDigest": identity_digest(identity),
        "commands": rows,
        "executedCount": 1,
        "failedCount": 0 if ok else 1,
        "omittedCount": 0,
        "risk": {"level": "high", "reason": "release_promotion_surface"},
    }
    return inventory


def test_missing_release_evidence_is_hold() -> None:
    verdict = verify_release_evidence(None, require=True)
    assert verdict["accepted"] is False
    assert verdict["code"] == "evidence_missing"
    decision = evaluate_release_path({"status": "passed", "testProfile": "release"}, _identity())
    assert decision.accepted is False
    assert decision.code == "evidence_missing"


def test_empty_release_evidence_is_hold() -> None:
    assert verify_release_evidence({}, require=True)["code"] == "evidence_empty"
    empty = {
        "schemaVersion": 1,
        "kind": EVIDENCE_KIND,
        "status": "passed",
        "testProfile": "release",
        "fullSuiteInvoked": False,
        "ok": True,
        "complete": True,
        "workspaceMutated": False,
        "identity": _identity(),
        "identityDigest": identity_digest(_identity()),
        "commands": [],
        "failedCount": 0,
    }
    assert evaluate_release_path(empty).code == "evidence_empty"
    with pytest.raises(ReleaseGateError) as caught:
        evidence_from_inventory({"profile": "release", "ok": True, "complete": True, "commands": [], "identity": _identity()})
    assert caught.value.code == "evidence_empty"


def test_stale_release_evidence_is_hold() -> None:
    evidence = evidence_from_inventory(_inventory())
    stale = evaluate_release_path(evidence, _identity(headCommit="c" * 40))
    assert stale.accepted is False
    assert stale.code == "evidence_stale"
    mutated = dict(evidence)
    mutated["identity"] = _identity(gitTree="d" * 40)
    assert verify_release_evidence(mutated, _identity())["code"] == "evidence_stale"


def test_failed_release_evidence_is_hold() -> None:
    evidence = evidence_from_inventory(_inventory(ok=False))
    assert evidence["ok"] is False
    assert evidence["status"] == "failed"
    decision = evaluate_release_path(evidence, _identity())
    assert decision.accepted is False
    assert decision.code == "release_gate_failed"


def test_successful_release_evidence_is_accepted_without_full_rerun() -> None:
    evidence = evidence_from_inventory(_inventory())
    assert evidence["kind"] == EVIDENCE_KIND
    assert evidence["fullSuiteInvoked"] is False
    decision = evaluate_release_path(evidence, _identity())
    assert decision.accepted is True
    assert decision.code == "accepted"
    assert "full-suite" in decision.detail


def test_full_suite_marker_is_rejected() -> None:
    with pytest.raises(ReleaseGateError) as caught:
        evidence_from_inventory(_inventory(), full_suite_invoked=True)
    assert caught.value.code == "full_suite_reentered"
    payload = evidence_from_inventory(_inventory())
    payload["fullSuiteInvoked"] = True
    assert evaluate_release_path(payload).code == "full_suite_reentered"
    with pytest.raises(ReleaseGateError) as caught_cmd:
        evidence_from_inventory(
            _inventory(commands=[["python3", "scripts/gitops/run_delivery_profile.py", "full"]])
        )
    assert caught_cmd.value.code == "full_suite_reentered"


def test_status_only_payload_remains_compatible_without_identity() -> None:
    decision = evaluate_release_path({"status": "passed", "testProfile": "release", "fullSuiteInvoked": False})
    assert decision.accepted is True
    assert decision.code == "accepted"


def test_repo_release_profile_is_non_empty_and_non_mutating(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    config_path, commands = load_profile(root, "release")
    assert config_path.name == "delivery.json"
    assert commands
    assert ["python3", "scripts/gitops/secret_scan.py"] in commands
    risk = classify_risk([], profile="release", commands=commands)
    assert risk["level"] != "critical"
    assert not risk["mutatingCommands"]
    mutating = classify_risk([], profile="release", commands=[["git", "reset", "--hard"]])
    assert mutating["level"] == "critical"
    inventory = run_profile(
        tmp_path,
        "release",
        config_path=config_path,
        commands=[["python3", "-c", "print('release-ok')"]],
        identity=_identity(),
    )
    assert inventory["ok"] is True
    assert inventory["profile"] == "release"


def test_empty_declared_release_commands_fail_closed(tmp_path: Path) -> None:
    config = tmp_path / ".ide-development" / "config" / "delivery.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps({"profiles": {"fast": {"commands": [["true"]]}, "full": {"commands": [["true"]]}, "release": {"commands": []}}}),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as caught:
        load_profile(tmp_path, "release")
    assert "delivery_profile_commands_missing" in str(caught.value)
    with pytest.raises(DeliveryProfileError):
        run_profile(tmp_path, "release", commands=[], identity=_identity())
