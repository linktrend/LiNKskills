#!/usr/bin/env python3
"""Exact-head Cursor Bugbot review-provider route (Skills consumer).

Trusted default-branch scripts request Bugbot for a sealed Phase PR after the
``Linktrend Full Suite`` job succeeds on that SHA. Candidate trees are never
executed. Mentions are authored only with ``LINKTREND_BUGBOT_USER_TOKEN``.

``GITHUB_TOKEN`` / App installation tokens must not post the mention: Cursor
Bugbot does not reliably wake on bot comments, and bash ``-f body=$'\\n'``
interpolation previously stored a literal backslash-n so ``@cursor review``
was not an executable trigger line.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from bugbot_user_credentials import (
        BugbotUserCredentialsError,
        require_bugbot_user_token,
        subprocess_env_for_token,
    )
    from delivery_modes import (
        DEFAULT_PHASE_PREFIX,
        is_phase_branch,
        is_valid_sha,
        normalize_sha,
    )
    from packager_logic import (
        DEFAULT_BUGBOT_COMMAND,
        build_bugbot_comment,
        has_executable_bugbot_trigger,
        should_request_bugbot,
    )
except ModuleNotFoundError:  # pragma: no cover - package-style execution
    from scripts.gitops.bugbot_user_credentials import (  # type: ignore
        BugbotUserCredentialsError,
        require_bugbot_user_token,
        subprocess_env_for_token,
    )
    from scripts.gitops.delivery_modes import (  # type: ignore
        DEFAULT_PHASE_PREFIX,
        is_phase_branch,
        is_valid_sha,
        normalize_sha,
    )
    from scripts.gitops.packager_logic import (  # type: ignore
        DEFAULT_BUGBOT_COMMAND,
        build_bugbot_comment,
        has_executable_bugbot_trigger,
        should_request_bugbot,
    )

FULL_SUITE_JOB_NAME = "Linktrend Full Suite"
DEVELOPMENT_BRANCH = "development"
ACTION_REQUEST = "request"
ACTION_SKIP = "skip"
ACTION_REJECT = "reject"


class ReviewProviderError(ValueError):
    """Fail-closed review-provider rejection."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail or code
        super().__init__(self.code if not detail else f"{self.code}: {self.detail}")


def _pr_head_sha(pr: Mapping[str, Any]) -> str:
    head = pr.get("head")
    if isinstance(head, Mapping):
        return normalize_sha(str(head.get("sha") or ""))
    return normalize_sha(str(pr.get("headSha") or pr.get("headRefOid") or ""))


def _pr_head_ref(pr: Mapping[str, Any]) -> str:
    head = pr.get("head")
    if isinstance(head, Mapping):
        ref = head.get("ref")
        if isinstance(ref, str):
            return ref
    return str(pr.get("headRef") or pr.get("headRefName") or "")


def _pr_base_ref(pr: Mapping[str, Any]) -> str:
    base = pr.get("base")
    if isinstance(base, Mapping):
        ref = base.get("ref")
        if isinstance(ref, str):
            return ref
    return str(pr.get("baseRef") or pr.get("baseRefName") or "")


def _pr_number(pr: Mapping[str, Any]) -> int:
    raw = pr.get("number")
    if isinstance(raw, int) and not isinstance(raw, bool):
        return raw
    raise ReviewProviderError("invalid_pr_number", str(raw))


def _as_list(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        for key in ("check_runs", "pulls", "items", "comments"):
            value = raw.get(key)
            if isinstance(value, list):
                return _as_list(value)
        raise ReviewProviderError("invalid_list_payload", "object")
    if not isinstance(raw, list):
        raise ReviewProviderError("invalid_list_payload", type(raw).__name__)
    if not raw:
        return []
    if all(isinstance(item, list) for item in raw):
        flat: list[Any] = []
        for page in raw:
            flat.extend(page)
        return flat
    if any(isinstance(item, list) for item in raw):
        raise ReviewProviderError("invalid_list_payload", "mixed_pages")
    return raw


def require_exact_head(expected: str, live: str) -> str:
    """Return the shared SHA or raise on mismatch / malformed identity."""
    if not is_valid_sha(expected):
        raise ReviewProviderError("invalid_expected_head", expected)
    if not is_valid_sha(live):
        raise ReviewProviderError("invalid_live_head", live)
    exp = normalize_sha(expected)
    got = normalize_sha(live)
    if exp != got:
        raise ReviewProviderError("stale_pr_head", f"expected={exp} live={got}")
    return exp


def select_exact_phase_pr(
    pulls: Sequence[Any],
    *,
    expected_head: str,
    development_branch: str = DEVELOPMENT_BRANCH,
    phase_prefix: str = DEFAULT_PHASE_PREFIX,
) -> dict[str, Any]:
    """Admit exactly one same-repository phase/* → development PR at expected_head."""
    head = normalize_sha(expected_head)
    if not is_valid_sha(head):
        raise ReviewProviderError("invalid_expected_head", expected_head)
    matches: list[dict[str, Any]] = []
    for raw in pulls:
        if not isinstance(raw, Mapping):
            continue
        if not is_phase_branch(_pr_head_ref(raw), phase_prefix):
            continue
        if _pr_base_ref(raw) != development_branch:
            continue
        if _pr_head_sha(raw) != head:
            continue
        matches.append(dict(raw))
    if not matches:
        raise ReviewProviderError("phase_pr_missing", head)
    if len(matches) > 1:
        raise ReviewProviderError(
            "phase_pr_ambiguous",
            ",".join(str(_pr_number(item)) for item in matches),
        )
    return matches[0]


def full_suite_succeeded_on_head(check_runs: Sequence[Any], *, expected_head: str) -> bool:
    """True when the named Full Suite job completed successfully on expected_head."""
    head = normalize_sha(expected_head)
    for raw in check_runs:
        if not isinstance(raw, Mapping):
            continue
        name = str(raw.get("name") or raw.get("context") or "").strip()
        if name != FULL_SUITE_JOB_NAME:
            continue
        item_head = normalize_sha(str(raw.get("head_sha") or raw.get("headSha") or ""))
        if item_head != head:
            continue
        conclusion = str(raw.get("conclusion") or "").strip().lower()
        if conclusion == "success":
            return True
    return False


def prepare_review_provider_request(
    *,
    repository: str,
    expected_head: str,
    pulls: Sequence[Any],
    comments: Sequence[Any],
    check_runs: Sequence[Any],
    command: str = DEFAULT_BUGBOT_COMMAND,
    expected_pr_number: int | None = None,
) -> dict[str, Any]:
    """Decide whether to post an executable Bugbot mention for one exact head.

    Historical marker-only comments (literal ``\\n``, bot author, missing ``@``)
    do not consume the request budget and do not skip a genuine mention.
    """
    repo = (repository or "").strip()
    if not repo or "/" not in repo:
        raise ReviewProviderError("invalid_repository", repository)
    head = require_exact_head(expected_head, expected_head)
    if not full_suite_succeeded_on_head(check_runs, expected_head=head):
        raise ReviewProviderError(
            "full_suite_required_for_exact_head",
            f"{FULL_SUITE_JOB_NAME} success missing for {head}",
        )
    pr = select_exact_phase_pr(pulls, expected_head=head)
    live = _pr_head_sha(pr)
    require_exact_head(head, live)
    pr_number = _pr_number(pr)
    if expected_pr_number is not None and pr_number != expected_pr_number:
        raise ReviewProviderError(
            "dispatch_pr_mismatch",
            f"expected={expected_pr_number} live={pr_number}",
        )
    comment_rows = [item for item in comments if isinstance(item, Mapping)]
    ok, reason = should_request_bugbot(
        comments=comment_rows,
        head_sha=head,
        fast_gate_ok=True,
    )
    body = build_bugbot_comment(command, head)
    if not has_executable_bugbot_trigger(body):
        raise ReviewProviderError("non_executable_bugbot_body", "built mention is not executable")
    if "\\n" in body.split("\n", 1)[0]:
        raise ReviewProviderError("literal_backslash_n_in_trigger", "built mention is not a real newline")
    action = ACTION_REQUEST if ok else ACTION_SKIP
    return {
        "action": action,
        "reason": reason,
        "body": body if ok else "",
        "headSha": head,
        "prNumber": pr_number,
        "headRef": _pr_head_ref(pr),
        "repository": repo,
        "fullSuiteJobName": FULL_SUITE_JOB_NAME,
    }


def post_bugbot_comment(*, repository: str, pr_number: int, body: str) -> dict[str, Any]:
    """POST the mention using the user token only. Never logs token material."""
    if not has_executable_bugbot_trigger(body):
        raise ReviewProviderError("non_executable_bugbot_body", "refusing to post a non-executable mention")
    try:
        token = require_bugbot_user_token("bugbot_comment")
    except BugbotUserCredentialsError as exc:
        raise ReviewProviderError("bugbot_user_credentials_blocked", str(exc)) from exc
    env = subprocess_env_for_token(token, role="bugbot_comment")
    payload = json.dumps({"body": body}).encode("utf-8")
    result = subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            f"repos/{repository}/issues/{pr_number}/comments",
            "--input",
            "-",
        ],
        input=payload,
        env=env,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", errors="replace")
        raise ReviewProviderError("bugbot_comment_post_failed", stderr.strip()[:300])
    return {"posted": True, "prNumber": pr_number}


def _load_json_arg(raw: str) -> Any:
    if raw == "-":
        return json.load(sys.stdin)
    path = Path(raw)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(raw)


def cmd_prepare(args: argparse.Namespace) -> int:
    try:
        pulls = _as_list(_load_json_arg(args.pulls_json))
        comments = _as_list(_load_json_arg(args.comments_json))
        check_runs = _as_list(_load_json_arg(args.check_runs_json))
        expected_pr = args.expected_pr_number if args.expected_pr_number else None
        out = prepare_review_provider_request(
            repository=args.repository,
            expected_head=args.expected_head,
            pulls=pulls,
            comments=comments,
            check_runs=check_runs,
            expected_pr_number=expected_pr,
        )
    except ReviewProviderError as exc:
        json.dump({"action": ACTION_REJECT, "reason": exc.code, "detail": exc.detail}, sys.stdout)
        print()
        return 1
    json.dump(out, sys.stdout)
    print()
    return 0 if out["action"] != ACTION_REJECT else 1


def cmd_post(args: argparse.Namespace) -> int:
    body = args.body
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    try:
        out = post_bugbot_comment(
            repository=args.repository,
            pr_number=args.pr_number,
            body=body,
        )
    except ReviewProviderError as exc:
        print(f"{exc.code}: {exc.detail}", file=sys.stderr)
        return 1
    json.dump(out, sys.stdout)
    print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="Decide whether to request Bugbot for one exact head")
    p.add_argument("--repository", required=True)
    p.add_argument("--expected-head", required=True)
    p.add_argument("--pulls-json", required=True)
    p.add_argument("--comments-json", required=True)
    p.add_argument("--check-runs-json", required=True)
    p.add_argument("--expected-pr-number", type=int, default=0)
    p.set_defaults(func=cmd_prepare)

    c = sub.add_parser("post", help="Post the executable mention with the user token")
    c.add_argument("--repository", required=True)
    c.add_argument("--pr-number", type=int, required=True)
    c.add_argument("--body", default="")
    c.add_argument("--body-file", default="")
    c.set_defaults(func=cmd_post)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
