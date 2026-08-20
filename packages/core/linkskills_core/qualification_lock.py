"""Immutable v0.2 qualification lock for catalog skills.

This module records published/qualified/retired identity for every on-disk
catalog skill. It does not execute skills, mint grants, or change
certification_state / skills_run authority.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

from .hashing import build_skill_bundle_manifest, eval_suite_file_hash, skill_release_hash
from .release_v2 import sha256

LOCK_REL = Path("catalog/qualification-lock.json")
CONTRACT_VERSION = "skills.lock.v0.2"
PROVIDER_CONTRACT = "skills.api.v0.2"
GIT_SHA = 40


class QualificationLockError(ValueError):
    """Fail-closed qualification lock error."""


def _git(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=str(repo_root), text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise QualificationLockError(f"git identity unavailable: {exc}") from exc


def discover_catalog_skill_dirs(repo_root: Path) -> list[Path]:
    skills_root = Path(repo_root) / "skills"
    if not skills_root.is_dir():
        raise QualificationLockError("skills catalog directory is missing")
    return sorted(
        path.parent.resolve()
        for path in skills_root.glob("*/SKILL.md")
        if path.is_file()
    )


def _decision_for(skill_dir: Path) -> tuple[str, str]:
    if not (skill_dir / "SKILL.md").is_file():
        return "retired", "missing_skill_md"
    if eval_suite_file_hash(skill_dir) is None:
        return "retired", "missing_eval_suite"
    return "qualified", ""


def build_skill_release_record(skill_dir: Path, *, provider_commit: str, provider_tree: str) -> dict[str, Any]:
    """Build one immutable release row. Does not claim sealed usable certification."""
    decision, reason = _decision_for(skill_dir)
    skill_id = skill_dir.name
    if decision == "retired":
        return {
            "skillId": skill_id,
            "version": "0.0.0",
            "path": f"skills/{skill_id}",
            "decision": "retired",
            "retirementReason": reason,
            "lifecycle": "retired",
            "qualification": "withdrawn",
            "availability": "withdrawn",
            "fragmentLevel": 0,
            "fragments": [],
        }

    bundle = build_skill_bundle_manifest(skill_dir)
    version = str(bundle["version"])
    release_id = f"{bundle['skill_id']}@{version}"
    files_digest = str(bundle["content_hash"])
    package_digest = sha256(
        {
            "release_id": release_id,
            "files_digest": files_digest,
            "contract_version": "skills-release/0.2",
        }
    )
    fragments = [
        {
            "fragmentId": item["fragment_id"],
            "fragmentLevel": int(item["disclosure_level"]),
            "path": item["path"],
            "digest": item["content_hash"],
        }
        for item in bundle["fragments"]
    ]
    return {
        "skillId": skill_id,
        "version": version,
        "path": f"skills/{skill_id}",
        "decision": "qualified",
        "lifecycle": "published",
        "qualification": "qualified",
        "availability": "available",
        "contractVersion": PROVIDER_CONTRACT,
        "providerCommit": provider_commit,
        "providerTree": provider_tree,
        "releaseHash": package_digest,
        "bundleHash": files_digest,
        "manifestHash": str(bundle["bundle_hash"]),
        "skillReleaseHash": skill_release_hash(skill_dir),
        "evalSuiteHash": bundle.get("eval_suite_hash"),
        "fileCount": bundle["file_count"],
        "fragmentLevel": 2,
        "fragments": fragments,
    }


def build_qualification_lock(
    repo_root: Path,
    *,
    provider_commit: str | None = None,
    provider_tree: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    commit = provider_commit or _git(root, "rev-parse", "HEAD")
    tree = provider_tree or _git(root, "rev-parse", "HEAD^{tree}")
    if len(commit) != GIT_SHA or len(tree) != GIT_SHA:
        raise QualificationLockError("provider git identity must be a 40-character SHA")
    skills = [build_skill_release_record(path, provider_commit=commit, provider_tree=tree) for path in discover_catalog_skill_dirs(root)]
    qualified = [row for row in skills if row["decision"] == "qualified"]
    retired = [row for row in skills if row["decision"] == "retired"]
    if len(skills) != len({row["skillId"] for row in skills}):
        raise QualificationLockError("duplicate skill identities in catalog")
    lock_digest = sha256(
        {
            "contractVersion": CONTRACT_VERSION,
            "providerCommit": commit,
            "providerTree": tree,
            "skillIds": [row["skillId"] for row in skills],
            "releaseHashes": [row.get("releaseHash") for row in skills],
        }
    )
    return {
        "contractVersion": CONTRACT_VERSION,
        "packet": "PKT-03",
        "issue": "ISS-04",
        "provider": {
            "repository": "linktrend/LiNKskills",
            "commit": commit,
            "tree": tree,
        },
        "skillCount": len(skills),
        "qualifiedCount": len(qualified),
        "retiredCount": len(retired),
        "lockDigest": lock_digest,
        "skills": skills,
    }


def write_qualification_lock(repo_root: Path, lock: Mapping[str, Any] | None = None) -> Path:
    root = Path(repo_root).resolve()
    payload = dict(lock) if lock is not None else build_qualification_lock(root)
    path = root / LOCK_REL
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


def load_qualification_lock(repo_root: Path) -> dict[str, Any]:
    path = Path(repo_root).resolve() / LOCK_REL
    if not path.is_file():
        raise QualificationLockError("qualification lock is missing")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QualificationLockError("qualification lock must be an object")
    return payload


def verify_qualification_lock(repo_root: Path, lock: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Recompute the lock and require an exact match of identities and digests."""
    root = Path(repo_root).resolve()
    actual = dict(lock) if lock is not None else load_qualification_lock(root)
    provider = actual.get("provider")
    if not isinstance(provider, dict):
        raise QualificationLockError("qualification lock provider pin is missing")
    commit = provider.get("commit")
    tree = provider.get("tree")
    if not isinstance(commit, str) or not isinstance(tree, str):
        raise QualificationLockError("qualification lock provider pin is malformed")
    expected = build_qualification_lock(root, provider_commit=commit, provider_tree=tree)
    if actual.get("contractVersion") != CONTRACT_VERSION:
        raise QualificationLockError("qualification lock contractVersion mismatch")
    if actual.get("provider") != expected["provider"]:
        raise QualificationLockError("qualification lock provider pin mismatch")
    actual_skills = actual.get("skills")
    if not isinstance(actual_skills, list) or len(actual_skills) != expected["skillCount"]:
        raise QualificationLockError("qualification lock does not cover every catalog skill")
    expected_by_id = {row["skillId"]: row for row in expected["skills"]}
    seen: set[str] = set()
    for row in actual_skills:
        if not isinstance(row, dict):
            raise QualificationLockError("qualification lock row is malformed")
        skill_id = row.get("skillId")
        if not isinstance(skill_id, str) or skill_id in seen:
            raise QualificationLockError("qualification lock skill identity is malformed")
        seen.add(skill_id)
        wanted = expected_by_id.get(skill_id)
        if wanted is None:
            raise QualificationLockError(f"unknown catalog skill in lock: {skill_id}")
        if row.get("decision") not in {"qualified", "retired"}:
            raise QualificationLockError(f"skill {skill_id} is neither qualified nor retired")
        if row.get("decision") == "qualified":
            for field in ("releaseHash", "bundleHash", "manifestHash", "version"):
                if row.get(field) != wanted.get(field):
                    raise QualificationLockError(f"skill {skill_id} digest mismatch on {field}")
        elif row.get("qualification") != "withdrawn":
            raise QualificationLockError(f"retired skill {skill_id} must withdraw qualification")
    missing = sorted(set(expected_by_id) - seen)
    if missing:
        raise QualificationLockError(f"lock missing catalog skills: {', '.join(missing)}")
    return expected
