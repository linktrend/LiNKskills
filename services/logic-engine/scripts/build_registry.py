#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from logic_engine.registry import build_registry_snapshot, write_registry_snapshot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic Logic Engine catalog from repo artifacts")
    parser.add_argument("--repo-root", default="../..", help="LiNKskills repository root")
    parser.add_argument("--manifest", default="manifest.json", help="Manifest path relative to repo root")
    parser.add_argument("--packages", default="config/packages.json", help="Package definition path")
    parser.add_argument("--output", default="generated/catalog.json", help="Output catalog path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    manifest_path = (repo_root / args.manifest).resolve()

    service_root = Path(__file__).resolve().parents[1]

    packages_path = Path(args.packages)
    if not packages_path.is_absolute():
        cwd_candidate = (Path.cwd() / packages_path).resolve()
        service_candidate = (service_root / packages_path).resolve()
        packages_path = cwd_candidate if cwd_candidate.exists() else service_candidate

    output_path = Path(args.output)
    if not output_path.is_absolute():
        cwd_candidate = (Path.cwd() / output_path).resolve()
        service_candidate = (service_root / output_path).resolve()
        output_path = cwd_candidate if cwd_candidate.parent.exists() else service_candidate

    result = build_registry_snapshot(repo_root, manifest_path, packages_path)
    write_registry_snapshot(result.snapshot, output_path)

    payload = {
        "status": "success",
        "manifest_entries": result.snapshot.manifest_entries,
        "capabilities": len(result.snapshot.capabilities),
        "packages": len(result.snapshot.packages),
        "output": str(output_path),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
