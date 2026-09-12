"""Exact-head review-provider route: executable mention, no bot/backslash-n skip."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.gitops.packager_logic import (
    build_bugbot_comment,
    has_executable_bugbot_trigger,
)
from scripts.gitops.review_provider_route import (
    ACTION_REJECT,
    ACTION_REQUEST,
    ACTION_SKIP,
    FULL_SUITE_JOB_NAME,
    ReviewProviderError,
    full_suite_succeeded_on_head,
    prepare_review_provider_request,
    post_bugbot_comment,
    select_exact_phase_pr,
)

ROOT = Path(__file__).resolve().parents[2]
HEAD = "cd2fd85552bf3fa3c2de5b9710306b31699321bb"
OTHER = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
WORKFLOW = ROOT / ".github/workflows/linktrend-review-provider.yml"
INTEGRATOR = ROOT / ".github/workflows/linktrend-integrator-merge.yml"


def _pr(*, number: int = 333, sha: str = HEAD, ref: str = "phase/ed-03-qualification") -> dict:
    return {
        "number": number,
        "head": {"sha": sha, "ref": ref},
        "base": {"ref": "development"},
    }


def _full_ok(*, sha: str = HEAD) -> dict:
    return {
        "name": FULL_SUITE_JOB_NAME,
        "head_sha": sha,
        "conclusion": "success",
    }


def _invalid_bot_comment(*, sha: str = HEAD) -> dict:
    # Observed on PR #333: github-actions[bot] + literal backslash-n.
    return {
        "user": {"login": "github-actions[bot]"},
        "body": f"@cursor review\\n<!-- linktrend-bugbot-requested: {sha} -->",
    }


class PackagerCommentRegressionTests(unittest.TestCase):
    def test_build_comment_is_executable_multiline(self) -> None:
        body = build_bugbot_comment("@cursor review", HEAD)
        self.assertIn("\n", body)
        self.assertTrue(has_executable_bugbot_trigger(body))
        first = body.split("\n", 1)[0]
        self.assertEqual(first.strip(), "@cursor review")
        self.assertNotIn("\\n", first)

    def test_literal_backslash_n_is_not_executable(self) -> None:
        body = _invalid_bot_comment()["body"]
        self.assertFalse(has_executable_bugbot_trigger(body))


class ReviewProviderPrepareTests(unittest.TestCase):
    def test_requests_despite_historical_non_executable_marker(self) -> None:
        out = prepare_review_provider_request(
            repository="linktrend/LiNKskills",
            expected_head=HEAD,
            pulls=[_pr()],
            comments=[_invalid_bot_comment()],
            check_runs=[_full_ok()],
        )
        self.assertEqual(out["action"], ACTION_REQUEST)
        self.assertEqual(out["prNumber"], 333)
        self.assertTrue(has_executable_bugbot_trigger(out["body"]))
        self.assertEqual(out["body"].split("\n", 1)[0].strip(), "@cursor review")

    def test_skips_duplicate_executable_mention(self) -> None:
        genuine = {"body": build_bugbot_comment("@cursor review", HEAD)}
        out = prepare_review_provider_request(
            repository="linktrend/LiNKskills",
            expected_head=HEAD,
            pulls=[_pr()],
            comments=[genuine],
            check_runs=[_full_ok()],
        )
        self.assertEqual(out["action"], ACTION_SKIP)
        self.assertEqual(out["reason"], "skipped_duplicate_marker")
        self.assertEqual(out["body"], "")

    def test_rejects_stale_phase_head(self) -> None:
        with self.assertRaises(ReviewProviderError) as ctx:
            prepare_review_provider_request(
                repository="linktrend/LiNKskills",
                expected_head=HEAD,
                pulls=[_pr(sha=OTHER)],
                comments=[],
                check_runs=[_full_ok()],
            )
        self.assertEqual(ctx.exception.code, "phase_pr_missing")

    def test_rejects_non_phase_branch(self) -> None:
        with self.assertRaises(ReviewProviderError) as ctx:
            prepare_review_provider_request(
                repository="linktrend/LiNKskills",
                expected_head=HEAD,
                pulls=[_pr(ref="issue/335-repair-ed-03-review-provider-route-for-exact-hea")],
                comments=[],
                check_runs=[_full_ok()],
            )
        self.assertEqual(ctx.exception.code, "phase_pr_missing")

    def test_rejects_missing_full_suite_success(self) -> None:
        with self.assertRaises(ReviewProviderError) as ctx:
            prepare_review_provider_request(
                repository="linktrend/LiNKskills",
                expected_head=HEAD,
                pulls=[_pr()],
                comments=[],
                check_runs=[
                    {
                        "name": FULL_SUITE_JOB_NAME,
                        "head_sha": HEAD,
                        "conclusion": "skipped",
                    }
                ],
            )
        self.assertEqual(ctx.exception.code, "full_suite_required_for_exact_head")

    def test_full_suite_match_is_exact_head(self) -> None:
        self.assertFalse(
            full_suite_succeeded_on_head([_full_ok(sha=OTHER)], expected_head=HEAD)
        )
        self.assertTrue(full_suite_succeeded_on_head([_full_ok()], expected_head=HEAD))

    def test_rejects_dispatch_pr_mismatch(self) -> None:
        with self.assertRaises(ReviewProviderError) as ctx:
            prepare_review_provider_request(
                repository="linktrend/LiNKskills",
                expected_head=HEAD,
                pulls=[_pr()],
                comments=[],
                check_runs=[_full_ok()],
                expected_pr_number=999,
            )
        self.assertEqual(ctx.exception.code, "dispatch_pr_mismatch")

    def test_select_requires_one_phase_pr(self) -> None:
        with self.assertRaises(ReviewProviderError) as ctx:
            select_exact_phase_pr([_pr(), _pr(number=334)], expected_head=HEAD)
        self.assertEqual(ctx.exception.code, "phase_pr_ambiguous")


class ReviewProviderPostTests(unittest.TestCase):
    def test_post_refuses_non_executable_body(self) -> None:
        with self.assertRaises(ReviewProviderError) as ctx:
            post_bugbot_comment(
                repository="linktrend/LiNKskills",
                pr_number=333,
                body=_invalid_bot_comment()["body"],
            )
        self.assertEqual(ctx.exception.code, "non_executable_bugbot_body")

    def test_post_uses_bugbot_comment_role_not_github_token(self) -> None:
        body = build_bugbot_comment("@cursor review", HEAD)
        captured: dict[str, str] = {}

        def _fake_require(operation: str) -> str:
            self.assertEqual(operation, "bugbot_comment")
            return "user-token-value"

        def _fake_env(token: str, *, role: str) -> dict[str, str]:
            self.assertEqual(token, "user-token-value")
            self.assertEqual(role, "bugbot_comment")
            env = {k: v for k, v in os.environ.items() if "TOKEN" not in k}
            env["GH_TOKEN"] = token
            captured.update(env)
            return env

        class _Result:
            returncode = 0
            stderr = b""

        def _fake_run(*args: object, **kwargs: object) -> _Result:
            env = kwargs.get("env") or {}
            self.assertEqual(env.get("GH_TOKEN"), "user-token-value")
            self.assertNotEqual(env.get("GH_TOKEN"), os.environ.get("GITHUB_TOKEN"))
            return _Result()

        with patch(
            "scripts.gitops.review_provider_route.require_bugbot_user_token",
            _fake_require,
        ), patch(
            "scripts.gitops.review_provider_route.subprocess_env_for_token",
            _fake_env,
        ), patch("scripts.gitops.review_provider_route.subprocess.run", _fake_run):
            out = post_bugbot_comment(
                repository="linktrend/LiNKskills", pr_number=333, body=body
            )
        self.assertTrue(out["posted"])
        self.assertEqual(captured.get("GH_TOKEN"), "user-token-value")


class WorkflowContractTests(unittest.TestCase):
    def test_provider_workflow_is_portal_style_default_branch(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("name: Linktrend Review Provider", text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", text)
        self.assertIn("review_provider_route.py prepare", text)
        self.assertIn("LINKTREND_BUGBOT_USER_TOKEN", text)
        self.assertIn("Linktrend Full Suite", text)
        self.assertNotIn('-f body="@cursor review\\n', text)
        self.assertIn("persist-credentials: false", text)

    def test_integrator_no_longer_posts_literal_backslash_n(self) -> None:
        text = INTEGRATOR.read_text(encoding="utf-8")
        self.assertNotIn('-f body="@cursor review\\n${marker}"', text)
        self.assertIn("review_provider_route_owns_mention", text)

    def test_prepare_cli_reject_is_json(self) -> None:
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "pulls.json").write_text("[]\n", encoding="utf-8")
            (tmp_path / "comments.json").write_text("[]\n", encoding="utf-8")
            (tmp_path / "checks.json").write_text("[]\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/gitops/review_provider_route.py"),
                    "prepare",
                    "--repository",
                    "linktrend/LiNKskills",
                    "--expected-head",
                    HEAD,
                    "--pulls-json",
                    str(tmp_path / "pulls.json"),
                    "--comments-json",
                    str(tmp_path / "comments.json"),
                    "--check-runs-json",
                    str(tmp_path / "checks.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["action"], ACTION_REJECT)
        self.assertEqual(payload["reason"], "full_suite_required_for_exact_head")


if __name__ == "__main__":
    unittest.main()
