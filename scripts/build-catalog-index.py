#!/usr/bin/env python3
"""Build catalog/index.json from on-disk skills (consumer discovery surface).

Certification state comes from the honest phase10 classification ledger overlay
(``evidence/phase10/skill-classification-draft.json``). Missing ledger entries
remain ``draft``. ``usable`` requires verified sealed live receipts (HMAC +
binding hashes), not nonempty evidence path strings alone.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from lib.skill_runtime.catalog import build_catalog_index, write_catalog_index
from lib.skill_runtime.catalog_provenance import validate_catalog_provenance
from lib.skill_runtime.certification_overlay import (
    load_certification_overlay,
    load_hash_overlay,
)


def _env_source_git_sha() -> Optional[str]:
    import os

    return os.environ.get("LINKSKILLS_CATALOG_GIT_SHA", "").strip() or None


def _env_source_tree_sha256() -> Optional[str]:
    import os

    return os.environ.get("LINKSKILLS_SOURCE_TREE_SHA256", "").strip() or None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Exit 1 if catalog/index.json is missing, stale vs skills, or "
            "provenance (git_sha / source_tree_sha256) fails"
        ),
    )
    parser.add_argument(
        "--no-overlay",
        action="store_true",
        help="Ignore classification ledger and emit draft for every skill",
    )
    parser.add_argument(
        "--git-sha",
        type=str,
        default=None,
        help=(
            "Governed source commit (ancestor). Defaults to "
            "LINKSKILLS_CATALOG_GIT_SHA or HEAD when inputs match."
        ),
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    overlay = {} if args.no_overlay else load_certification_overlay(repo_root)
    hashes = {} if args.no_overlay else load_hash_overlay(repo_root)
    source_git_sha = args.git_sha or _env_source_git_sha()
    source_tree = _env_source_tree_sha256()

    out_path = repo_root / "catalog" / "index.json"
    if args.check:
        if not out_path.is_file():
            print("catalog/index.json missing; run without --check to generate", file=sys.stderr)
            return 1
        import json

        existing = json.loads(out_path.read_text(encoding="utf-8"))
        provenance_errors = validate_catalog_provenance(existing, repo_root)
        if provenance_errors:
            for err in provenance_errors:
                print(f"catalog provenance: {err}", file=sys.stderr)
            return 1

        # Rebuild for skill-identity comparison using the catalog's source commit.
        index = build_catalog_index(
            repo_root,
            certification_overlay=overlay,
            hash_overlay=hashes,
            git_sha=existing.get("git_sha") or source_git_sha,
            source_tree_sha256=existing.get("source_tree_sha256") or source_tree,
            require_provenance=True,
        )
        # Compare skill identity + certification_state + release_hash + profile_hash
        # (ignore generated_at churn). Drift of sealed hashes fails --check.
        def _identity(s: dict) -> tuple:
            return (
                s["skill_id"],
                s["version"],
                s["path"],
                s["eval_suite_ref"],
                s.get("certification_state", "draft"),
                s.get("release_hash") or s.get("skill_release_hash") or "",
                s.get("profile_hash") or "",
            )

        existing_skills = {_identity(s) for s in existing.get("skills", [])}
        fresh_skills = {_identity(s) for s in index["skills"]}
        if existing_skills != fresh_skills:
            print(
                "catalog/index.json is stale; regenerate with scripts/build-catalog-index.py",
                file=sys.stderr,
            )
            return 1
        if existing.get("source_tree_sha256") != index.get("source_tree_sha256"):
            print(
                "catalog/index.json source_tree_sha256 drifted; regenerate",
                file=sys.stderr,
            )
            return 1
        usable = sum(1 for s in existing.get("skills", []) if s.get("certification_state") == "usable")
        print(
            f"catalog/index.json is current ({len(fresh_skills)} skills, usable={usable}, "
            f"source_tree_sha256={existing.get('source_tree_sha256')})"
        )
        return 0

    index = build_catalog_index(
        repo_root,
        certification_overlay=overlay,
        hash_overlay=hashes,
        git_sha=source_git_sha,
        source_tree_sha256=source_tree,
        require_provenance=True,
    )
    written = write_catalog_index(repo_root, index)
    usable = sum(1 for s in index["skills"] if s.get("certification_state") == "usable")
    print(
        f"Wrote {written} ({index['skill_count']} skills, usable={usable}, "
        f"git_sha={index.get('git_sha')}, source_tree_sha256={index.get('source_tree_sha256')})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
