#!/usr/bin/env python3
"""Build catalog/index.json from on-disk skills (consumer discovery surface).

Certification state comes from the honest phase10 classification ledger overlay
(``evidence/phase10/skill-classification-draft.json``). Missing ledger entries
remain ``draft``. ``usable`` requires sealed receipt evidence paths in the ledger.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from lib.skill_runtime.catalog import build_catalog_index, write_catalog_index
from lib.skill_runtime.certification_overlay import (
    load_certification_overlay,
    load_hash_overlay,
)


def _git_sha(repo_root: Path) -> Optional[str]:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            .strip()
            or None
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if catalog/index.json is missing or stale vs current skills",
    )
    parser.add_argument(
        "--no-overlay",
        action="store_true",
        help="Ignore classification ledger and emit draft for every skill",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    overlay = {} if args.no_overlay else load_certification_overlay(repo_root)
    hashes = {} if args.no_overlay else load_hash_overlay(repo_root)
    index = build_catalog_index(
        repo_root,
        certification_overlay=overlay,
        hash_overlay=hashes,
        git_sha=_git_sha(repo_root),
    )

    out_path = repo_root / "catalog" / "index.json"
    if args.check:
        if not out_path.is_file():
            print("catalog/index.json missing; run without --check to generate", file=sys.stderr)
            return 1
        import json

        existing = json.loads(out_path.read_text(encoding="utf-8"))
        # Compare skill identity + certification_state (ignore generated_at / git_sha churn).
        existing_skills = {
            (
                s["skill_id"],
                s["version"],
                s["path"],
                s["eval_suite_ref"],
                s.get("certification_state", "draft"),
            )
            for s in existing.get("skills", [])
        }
        fresh_skills = {
            (
                s["skill_id"],
                s["version"],
                s["path"],
                s["eval_suite_ref"],
                s.get("certification_state", "draft"),
            )
            for s in index["skills"]
        }
        if existing_skills != fresh_skills:
            print(
                "catalog/index.json is stale; regenerate with scripts/build-catalog-index.py",
                file=sys.stderr,
            )
            return 1
        usable = sum(1 for s in existing.get("skills", []) if s.get("certification_state") == "usable")
        print(
            f"catalog/index.json is current ({len(fresh_skills)} skills, usable={usable})"
        )
        return 0

    written = write_catalog_index(repo_root, index)
    usable = sum(1 for s in index["skills"] if s.get("certification_state") == "usable")
    print(f"Wrote {written} ({index['skill_count']} skills, usable={usable})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
