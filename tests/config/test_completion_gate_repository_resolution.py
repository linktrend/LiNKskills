from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "gitops" / "completion_gate.py"
SPEC = importlib.util.spec_from_file_location("completion_gate_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
completion_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(completion_gate)


def test_accepts_exact_github_https_and_ssh_remotes() -> None:
    parse = completion_gate.github_owner_repo_from_remote

    assert parse("https://github.com/linktrend/LiNKskills.git") == "linktrend/LiNKskills"
    assert parse("https://user:token@github.com/linktrend/LiNKskills.git") == "linktrend/LiNKskills"
    assert parse("git@github.com:linktrend/LiNKskills.git") == "linktrend/LiNKskills"
    assert parse("ssh://git@github.com/linktrend/LiNKskills.git") == "linktrend/LiNKskills"


def test_rejects_github_substrings_and_ambiguous_paths() -> None:
    parse = completion_gate.github_owner_repo_from_remote

    rejected = [
        "https://evil.example/github.com/linktrend/LiNKskills.git",
        "https://github.com.evil.example/linktrend/LiNKskills.git",
        "http://github.com/linktrend/LiNKskills.git",
        "https://github.com/linktrend/LiNKskills/extra.git",
        "https://github.com/linktrend/LiNKskills.git?token_fixture=redacted",
        "https://github.com/linktrend/../LiNKskills.git",
        "ssh://other@github.com/linktrend/LiNKskills.git",
    ]

    assert all(parse(remote) is None for remote in rejected)
