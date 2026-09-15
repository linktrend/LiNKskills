"""Identity-binding Phase integrator validation and eligibility."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.coordinator.state import CandidateIdentity
from scripts.gitops.delivery_modes import MODE_PHASE_INTEGRATION, validate_phase_delivery_record
from scripts.gitops.phase_integrator import (
    IssueTip,
    PhaseIntegrator,
    phase_merge_eligibility,
    seal_exact_phase_pr,
)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return (result.stdout or "").strip()


class PhaseIntegratorIdentityBindingTests(unittest.TestCase):
    def _repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, str], dict]:
        tmp = tempfile.TemporaryDirectory()
        repo = Path(tmp.name)
        git(repo, "init", "-q", "-b", "development")
        git(repo, "config", "user.email", "integrator@example.invalid")
        git(repo, "config", "user.name", "integrator tests")
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", "base.txt")
        git(repo, "commit", "-qm", "base")
        base = git(repo, "rev-parse", "HEAD")
        git(repo, "checkout", "-qb", "issue/41-part")
        (repo / "issue.txt").write_text("issue\n", encoding="utf-8")
        git(repo, "add", "issue.txt")
        git(repo, "commit", "-qm", "issue 41")
        issue = git(repo, "rev-parse", "HEAD")
        git(repo, "checkout", "-qb", "phase/next", "development")
        git(repo, "merge", "--no-ff", "--no-edit", "-m", "phase: include issue/41-part", issue)
        package = git(repo, "rev-parse", "HEAD")
        package_tree = git(repo, "rev-parse", "HEAD^{tree}")
        record = {
            "schemaVersion": 1,
            "kind": "phase-record",
            "deliveryMode": MODE_PHASE_INTEGRATION,
            "phaseId": "next",
            "phaseBranch": "phase/next",
            "baseSha": base,
            "immutableBaseSha": base,
            "headSha": package,
            "gitTree": package_tree,
            "mergeSha": None,
            "sealed": False,
            "sealRevision": 0,
            "acceptedIssues": [
                {
                    "branch": "issue/41-part",
                    "sha": issue,
                    "accepted": True,
                    "included": True,
                    "acceptanceSha": issue,
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
        tip_tree = git(repo, "rev-parse", "HEAD^{tree}")
        shas = {
            "base": base,
            "package": package,
            "package_tree": package_tree,
            "issue": issue,
            "tip": tip,
            "tip_tree": tip_tree,
        }
        return tmp, repo, shas, record

    def test_validator_and_eligibility_for_identity_binding_tip(self) -> None:
        tmp, repo, shas, record = self._repo()
        self.addCleanup(tmp.cleanup)
        ok, detail = validate_phase_delivery_record(
            record, branch="phase/next", head_sha=shas["tip"], repo=repo
        )
        self.assertTrue(ok, detail)
        integrator = PhaseIntegrator(
            repo,
            repository="owner/name",
            phase_branch="phase/next",
            phase_id="next",
            immutable_base_sha=shas["base"],
        )
        integrator._write(record)
        identity = CandidateIdentity("owner/name", shas["tip"], shas["tip_tree"], {}, "full")
        sealed = integrator.seal(head_sha=shas["tip"], candidate_identity=identity)
        self.assertEqual(sealed["headSha"], shas["package"])
        self.assertEqual(sealed["sealedSha"], shas["tip"])
        self.assertNotEqual(sealed["headSha"], sealed["sealedSha"])
        sealed["fast"] = {"status": "passed", "sha": shas["tip"]}
        sealed["bugbot"] = {"status": "passed", "sha": shas["tip"]}
        sealed["full"] = {"status": "not-required"}
        verdict = phase_merge_eligibility(sealed, live_head_sha=shas["tip"], repo=repo)
        self.assertTrue(verdict.eligible, verdict.detail)
        self.assertTrue(verdict.checks["liveHeadUnchanged"])

    def test_seal_exact_phase_pr_retains_assembled_parent(self) -> None:
        tmp, repo, shas, record = self._repo()
        self.addCleanup(tmp.cleanup)
        packager_dir = Path(git(repo, "rev-parse", "--git-common-dir"))
        if not packager_dir.is_absolute():
            packager_dir = (repo / packager_dir).resolve()
        dest = packager_dir / "ide-development" / "phase-packager" / "next"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "phase-delivery-record.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        payload = {
            "number": 9,
            "state": "open",
            "html_url": "https://github.com/owner/name/pull/9",
            "draft": True,
            "head": {"sha": shas["tip"], "ref": "phase/next", "repo": {"full_name": "owner/name"}},
            "base": {"ref": "development", "sha": shas["base"]},
        }
        result = seal_exact_phase_pr(
            repo=repo,
            repository="owner/name",
            pr_number=9,
            expected_head=shas["tip"],
            expected_tree=shas["tip_tree"],
            issues=[IssueTip("issue/41-part", shas["issue"], acceptance_sha=shas["issue"], included=True)],
            pr_payload=payload,
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["merged"])
        self.assertFalse(result["fullDispatched"])
        self.assertFalse(result["deployed"])
        loaded = json.loads((dest / "phase-delivery-record.json").read_text(encoding="utf-8"))
        # Isolated integrator record is the destination; packager copy is updated after seal.
        integrator_record = json.loads(
            (
                packager_dir / "ide-development" / "phase-integrator" / "next" / "phase-delivery-record.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(integrator_record["headSha"], shas["package"])
        self.assertEqual(integrator_record["sealedSha"], shas["tip"])
        self.assertEqual(integrator_record["gitTree"], shas["package_tree"])
        ok, detail = validate_phase_delivery_record(
            {**integrator_record, "sealed": False, "sealedSha": None, "candidateIdentity": None},
            branch="phase/next",
            head_sha=shas["tip"],
            repo=repo,
        )
        self.assertTrue(ok, detail)
        self.assertIsNotNone(loaded)


if __name__ == "__main__":
    unittest.main()
