"""Committed proof for Integrator seal_exact_phase_pr (ED-03 repair).

Covers idempotence, stale head/tree, non-integrator mutation, and the
no-merge / no-full / no-deploy contract. Seal behavior is exercised without
changing PhaseIntegrator.seal.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest

from scripts.gitops.phase_integrator import (
    INTEGRATOR_ROLE,
    PhaseLifecycleError,
    isolated_record_path,
    main as integrator_main,
    seal_exact_phase_pr,
)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout or "git failed")
    return (result.stdout or "").strip()


def _phase_repo() -> tuple[tempfile.TemporaryDirectory[str], Path, str, str, str, str]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _git(root, "init", "-q", "-b", "development")
    _git(root, "config", "user.email", "tests@example.invalid")
    _git(root, "config", "user.name", "ED-03 seal tests")
    (root / "base.txt").write_text("base\n", encoding="utf-8")
    _git(root, "add", "base.txt")
    _git(root, "commit", "-qm", "base")
    base = _git(root, "rev-parse", "HEAD")
    _git(root, "checkout", "-qb", "phase/demo")
    (root / "issue-1.txt").write_text("issue 1\n", encoding="utf-8")
    _git(root, "add", "issue-1.txt")
    _git(root, "commit", "-qm", "issue 1")
    head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    return tmp, root, base, head, tree, head


def _pr_payload(*, number: int, head: str, base: str, repository: str = "owner/name") -> dict[str, Any]:
    return {
        "number": number,
        "state": "open",
        "html_url": f"https://github.com/{repository}/pull/{number}",
        "draft": True,
        "head": {"sha": head, "ref": "phase/demo", "repo": {"full_name": repository}},
        "base": {"ref": "development", "sha": base},
    }


def _seal(
    root: Path,
    *,
    head: str,
    tree: str,
    base: str,
    actor: str = INTEGRATOR_ROLE,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "repo": root,
        "repository": "owner/name",
        "pr_number": 7,
        "expected_head": head,
        "expected_tree": tree,
        "issues": [f"issue/1-part@{head}"],
        "pr_payload": _pr_payload(number=7, head=head, base=base),
        "actor": actor,
    }
    if extra:
        kwargs.update(extra)
    return seal_exact_phase_pr(**kwargs)


def test_seal_is_idempotent_for_matching_head_and_tree() -> None:
    tmp, root, base, head, tree, issue_sha = _phase_repo()
    with tmp:
        first = _seal(root, head=head, tree=tree, base=base)
        assert first["ok"] is True
        assert first["action"] == "sealed"
        assert first["sealed"] is True
        assert first["sealedSha"] == head
        assert first["sealRevision"] == 1
        first_candidate = first["candidateId"]

        second = _seal(root, head=head, tree=tree, base=base)
        assert second["ok"] is True
        assert second["action"] == "already_sealed"
        assert second["sealed"] is True
        assert second["sealedSha"] == head
        assert second["sealRevision"] == 1
        assert second["candidateId"] == first_candidate
        assert second["headSha"] == head
        assert second["gitTree"] == tree
        assert _git(root, "rev-parse", "HEAD") == head
        assert _git(root, "rev-parse", "HEAD^{tree}") == tree


def test_seal_rejects_stale_expected_head() -> None:
    tmp, root, base, head, tree, _issue = _phase_repo()
    with tmp:
        with pytest.raises(PhaseLifecycleError, match="stale_phase_head"):
            seal_exact_phase_pr(
                repo=root,
                repository="owner/name",
                pr_number=7,
                expected_head=base,
                expected_tree=tree,
                issues=[f"issue/1-part@{head}"],
                pr_payload=_pr_payload(number=7, head=head, base=base),
            )


def test_seal_rejects_stale_expected_tree() -> None:
    tmp, root, base, head, tree, _issue = _phase_repo()
    with tmp:
        stale_tree = _git(root, "rev-parse", f"{base}^{{tree}}")
        assert stale_tree != tree
        with pytest.raises(PhaseLifecycleError, match="stale_phase_tree"):
            seal_exact_phase_pr(
                repo=root,
                repository="owner/name",
                pr_number=7,
                expected_head=head,
                expected_tree=stale_tree,
                issues=[f"issue/1-part@{head}"],
                pr_payload=_pr_payload(number=7, head=head, base=base),
            )


def test_seal_rejects_stale_recorded_head_and_tree() -> None:
    tmp, root, base, head, tree, _issue = _phase_repo()
    with tmp:
        first = _seal(root, head=head, tree=tree, base=base)
        assert first["action"] == "sealed"
        (root / "late.txt").write_text("late\n", encoding="utf-8")
        _git(root, "add", "late.txt")
        _git(root, "commit", "-qm", "late phase movement")
        moved = _git(root, "rev-parse", "HEAD")
        moved_tree = _git(root, "rev-parse", "HEAD^{tree}")
        assert moved != head
        with pytest.raises(PhaseLifecycleError, match="stale_phase_head"):
            seal_exact_phase_pr(
                repo=root,
                repository="owner/name",
                pr_number=7,
                expected_head=moved,
                expected_tree=moved_tree,
                issues=[f"issue/1-part@{head}"],
                pr_payload=_pr_payload(number=7, head=moved, base=base),
            )
        record_path = isolated_record_path(root, "phase/demo", kind="integrator")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["headSha"] = head
        record["gitTree"] = "0" * 40
        record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        packager_path = isolated_record_path(root, "phase/demo", kind="packager")
        if packager_path.is_file():
            packager_path.unlink()
        with pytest.raises(PhaseLifecycleError, match="stale_phase_tree"):
            seal_exact_phase_pr(
                repo=root,
                repository="owner/name",
                pr_number=7,
                expected_head=head,
                expected_tree=tree,
                issues=[f"issue/1-part@{head}"],
                pr_payload=_pr_payload(number=7, head=head, base=base),
            )


def test_seal_rejects_non_integrator_actor() -> None:
    tmp, root, base, head, tree, _issue = _phase_repo()
    with tmp:
        with pytest.raises(PhaseLifecycleError, match="non_integrator_mutation"):
            _seal(root, head=head, tree=tree, base=base, actor="packager")
        with pytest.raises(PhaseLifecycleError, match="non_integrator_mutation"):
            _seal(root, head=head, tree=tree, base=base, actor="worker")
        assert isolated_record_path(root, "phase/demo", kind="integrator").is_file() is False


def test_seal_does_not_merge_dispatch_full_or_deploy() -> None:
    tmp, root, base, head, tree, _issue = _phase_repo()
    with tmp:
        commits_before = _git(root, "rev-list", "--count", "HEAD")
        result = _seal(root, head=head, tree=tree, base=base)
        assert result["merged"] is False
        assert result["fullDispatched"] is False
        assert result["deployed"] is False
        assert result["component"] == "phase_integrator"
        record = json.loads(Path(result["recordPath"]).read_text(encoding="utf-8"))
        assert record["merged"] is False
        assert record["fullDispatched"] is False
        assert record["deployed"] is False
        assert record.get("mergeSha") is None
        assert record["full"]["status"] == "not-run"
        assert _git(root, "rev-parse", "HEAD") == head
        assert _git(root, "rev-list", "--count", "HEAD") == commits_before

        repeated = _seal(root, head=head, tree=tree, base=base)
        assert repeated["action"] == "already_sealed"
        assert repeated["merged"] is False
        assert repeated["fullDispatched"] is False
        assert repeated["deployed"] is False


def test_seal_cli_preserves_no_merge_full_deploy_contract(tmp_path: Path) -> None:
    tmp, root, base, head, tree, _issue = _phase_repo()
    with tmp:
        payload_path = tmp_path / "pr.json"
        payload_path.write_text(json.dumps(_pr_payload(number=9, head=head, base=base)), encoding="utf-8")
        code = integrator_main(
            [
                "seal",
                "--repository",
                "owner/name",
                "--pr",
                "9",
                "--expected-head",
                head,
                "--expected-tree",
                tree,
                "--repo-path",
                str(root),
                "--accept",
                f"issue/1-part@{head}",
                "--pr-json",
                str(payload_path),
            ]
        )
        assert code == 0
        record_path = isolated_record_path(root, "phase/demo", kind="integrator")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        assert record["sealed"] is True
        assert record["merged"] is False
        assert record["fullDispatched"] is False
        assert record["deployed"] is False
        assert record["headSha"] == head
        assert record["gitTree"] == tree
