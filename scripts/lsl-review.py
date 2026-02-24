#!/usr/bin/env python3
"""Review dev-* branches, run validator, and optionally merge safe branches into local main."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def run(cmd: List[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=check)


def ensure_git_repo(repo_root: Path) -> None:
    proc = run(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo_root, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{repo_root} is not a git repository")


def list_remote_dev_branches(repo_root: Path, remote: str) -> List[str]:
    run(["git", "fetch", remote, "--prune"], cwd=repo_root, check=True)
    proc = run(
        ["git", "for-each-ref", "--format=%(refname:short)", f"refs/remotes/{remote}/dev-*"],
        cwd=repo_root,
        check=True,
    )
    branches = []
    for line in proc.stdout.splitlines():
        ref = line.strip()
        if not ref:
            continue
        prefix = f"{remote}/"
        if ref.startswith(prefix):
            branches.append(ref[len(prefix) :])
    return sorted(set(branches))


def verify_gw_syntax(repo_root: Path) -> Dict[str, Any]:
    """Verify internalized GW source structure and Python syntax."""
    gw_root = repo_root / "tools" / "gw" / "src"
    services_dir = gw_root / "services"
    utils_dir = gw_root / "utils"
    required_files = [gw_root / "cli.py", gw_root / "requirements.txt"]
    required_dirs = [services_dir, utils_dir]

    missing_paths = [str(p.relative_to(repo_root)) for p in required_files + required_dirs if not p.exists()]
    if missing_paths:
        return {
            "gw_syntax_exit_code": 1,
            "gw_syntax_output": f"Missing required internalized GW paths: {', '.join(missing_paths)}",
            "gw_checked_files": [],
        }

    python_files = [gw_root / "cli.py"]
    python_files.extend(sorted(services_dir.rglob("*.py")))
    python_files.extend(sorted(utils_dir.rglob("*.py")))
    checked_files = [str(path.relative_to(repo_root)) for path in python_files]

    if not python_files:
        return {
            "gw_syntax_exit_code": 1,
            "gw_syntax_output": "No Python files found for GW syntax verification.",
            "gw_checked_files": [],
        }

    proc = run(["python3", "-m", "py_compile", *[str(path) for path in python_files]], cwd=repo_root, check=False)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    if not output:
        output = f"Validated syntax for {len(python_files)} GW Python files."
    return {
        "gw_syntax_exit_code": proc.returncode,
        "gw_syntax_output": output,
        "gw_checked_files": checked_files,
    }


def validate_branch(repo_root: Path, remote: str, branch: str) -> Dict[str, Any]:
    branch_ref = f"{remote}/{branch}"
    with tempfile.TemporaryDirectory(prefix="lsl-review-") as tmp:
        worktree = Path(tmp)
        add_proc = run(["git", "worktree", "add", "--detach", str(worktree), branch_ref], cwd=repo_root, check=False)
        if add_proc.returncode != 0:
            return {
                "branch": branch,
                "validator_exit_code": add_proc.returncode,
                "validator_output": (add_proc.stderr or add_proc.stdout).strip(),
                "gw_syntax_exit_code": 1,
                "gw_syntax_output": "Skipped due to worktree checkout failure.",
                "gw_checked_files": [],
                "ready_for_merge": False,
            }

        try:
            validator_proc = run(
                ["python3", "validator.py", "--repo-root", ".", "--scan-all"],
                cwd=worktree,
                check=False,
            )
            combined = (validator_proc.stdout + "\n" + validator_proc.stderr).strip()
            gw_check = verify_gw_syntax(worktree)
            ready_for_merge = validator_proc.returncode == 0 and gw_check["gw_syntax_exit_code"] == 0
            return {
                "branch": branch,
                "validator_exit_code": validator_proc.returncode,
                "validator_output": combined,
                "gw_syntax_exit_code": gw_check["gw_syntax_exit_code"],
                "gw_syntax_output": gw_check["gw_syntax_output"],
                "gw_checked_files": gw_check["gw_checked_files"],
                "ready_for_merge": ready_for_merge,
            }
        finally:
            run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo_root, check=False)


def generate_sync_report(repo_root: Path, remote: str) -> Dict[str, Any]:
    branches = list_remote_dev_branches(repo_root, remote)
    results = [validate_branch(repo_root, remote, branch) for branch in branches]
    safe = [entry["branch"] for entry in results if entry.get("ready_for_merge")]
    return {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo_root": str(repo_root),
        "remote": remote,
        "branches_checked": len(branches),
        "results": results,
        "safe_branches": safe,
    }


def merge_all_safe(repo_root: Path, safe_branches: List[str], remote: str = "origin") -> Dict[str, Any]:
    merge_results: List[Dict[str, Any]] = []
    if not safe_branches:
        return {"merged": [], "status": "no-safe-branches"}

    run(["git", "checkout", "main"], cwd=repo_root, check=True)
    run(["git", "pull", "--ff-only", remote, "main"], cwd=repo_root, check=True)

    for branch in safe_branches:
        proc = run(["git", "merge", "--no-ff", f"{remote}/{branch}", "-m", f"merge: {branch}"], cwd=repo_root, check=False)
        ok = proc.returncode == 0
        merge_results.append(
            {
                "branch": branch,
                "merged": ok,
                "output": (proc.stdout + "\n" + proc.stderr).strip(),
            }
        )
        if not ok:
            run(["git", "merge", "--abort"], cwd=repo_root, check=False)
            return {"merged": merge_results, "status": "stopped-on-conflict"}

    return {"merged": merge_results, "status": "success"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run validator across remote dev-* branches and produce sync report JSON")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--remote", default="origin", help="Git remote name")
    parser.add_argument("--output", default="", help="Optional path to write sync report JSON")
    parser.add_argument("--merge-safe", action="store_true", help="Merge safe branches into local main")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    ensure_git_repo(repo_root)

    report = generate_sync_report(repo_root, args.remote)
    if args.merge_safe:
        report["merge_result"] = merge_all_safe(repo_root, report.get("safe_branches", []), args.remote)

    payload = json.dumps(report, indent=2)
    print(payload)

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
