"""Identity-binding Phase delivery record validation."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.delivery_modes import (
    MODE_PHASE_INTEGRATION,
    bind_phase_identity_fields,
    validate_phase_delivery_record,
)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return (result.stdout or "").strip()


class DeliveryModeIdentityBindingTests(unittest.TestCase):
    def _identity_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, str], dict]:
        tmp = tempfile.TemporaryDirectory()
        repo = Path(tmp.name)
        git(repo, "init", "-q", "-b", "development")
        git(repo, "config", "user.email", "modes@example.invalid")
        git(repo, "config", "user.name", "delivery modes tests")
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", "base.txt")
        git(repo, "commit", "-qm", "base")
        base = git(repo, "rev-parse", "HEAD")
        git(repo, "checkout", "-qb", "phase/next")
        (repo / "issue.txt").write_text("issue\n", encoding="utf-8")
        git(repo, "add", "issue.txt")
        git(repo, "commit", "-qm", "issue 41")
        package = git(repo, "rev-parse", "HEAD")
        package_tree = git(repo, "rev-parse", "HEAD^{tree}")
        issue_sha = package
        record = {
            "schemaVersion": 1,
            "deliveryMode": MODE_PHASE_INTEGRATION,
            "phaseBranch": "phase/next",
            "baseSha": base,
            "headSha": package,
            "gitTree": package_tree,
            "mergeSha": None,
            "sealed": False,
            "acceptedIssues": [
                {
                    "branch": "issue/41-part",
                    "sha": issue_sha,
                    "accepted": True,
                    "included": True,
                    "acceptanceSha": issue_sha,
                }
            ],
            "namedGateEvidence": {
                "gate": "fast-gate",
                "sha": package,
                "status": "missing",
                "detail": "unsealed_phase_pr",
                "checks": [],
            },
        }
        dest = repo / ".linktrend" / "phase-delivery-record.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        git(repo, "add", "-f", "--", ".linktrend/phase-delivery-record.json")
        git(repo, "commit", "-qm", "phase: commit delivery record")
        tip = git(repo, "rev-parse", "HEAD")
        shas = {"base": base, "package": package, "tip": tip, "issue": issue_sha}
        return tmp, repo, shas, record

    def test_validator_accepts_identity_binding_tip(self) -> None:
        tmp, repo, shas, record = self._identity_repo()
        self.addCleanup(tmp.cleanup)
        ok, detail = validate_phase_delivery_record(
            record,
            branch="phase/next",
            head_sha=shas["tip"],
            repo=repo,
        )
        self.assertTrue(ok, detail)
        bound, bind_detail = bind_phase_identity_fields(
            record, assembled_sha=shas["package"], tip_sha=shas["tip"]
        )
        self.assertTrue(bound, bind_detail)

    def test_validator_rejects_self_referential_tip_identity(self) -> None:
        tmp, repo, shas, record = self._identity_repo()
        self.addCleanup(tmp.cleanup)
        forged = dict(record)
        forged["headSha"] = shas["tip"]
        ok, detail = validate_phase_delivery_record(
            forged,
            branch="phase/next",
            head_sha=shas["tip"],
            repo=repo,
        )
        self.assertFalse(ok)
        self.assertIn("parent", detail.replace("self_referential", "assembled_parent"))

    def test_legacy_record_without_repo_still_names_the_tip(self) -> None:
        sha = "a" * 40
        record = {
            "schemaVersion": 1,
            "deliveryMode": MODE_PHASE_INTEGRATION,
            "phaseBranch": "phase/next",
            "baseSha": "b" * 40,
            "headSha": sha,
            "mergeSha": None,
            "acceptedIssues": [
                {"branch": "issue/1-alpha", "sha": "c" * 40, "accepted": True, "included": True}
            ],
            "namedGateEvidence": {"gate": "fast-gate", "sha": sha, "status": "missing", "checks": []},
        }
        ok, detail = validate_phase_delivery_record(record, branch="phase/next", head_sha=sha)
        self.assertTrue(ok, detail)
        ok_unproven, detail_unproven = validate_phase_delivery_record(
            record, branch="phase/next", head_sha="d" * 40
        )
        self.assertFalse(ok_unproven)
        self.assertEqual(detail_unproven, "phase_delivery_assembled_parent_unproven")


if __name__ == "__main__":
    unittest.main()
