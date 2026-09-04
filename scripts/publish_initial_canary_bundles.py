#!/usr/bin/env python3
"""Publish initial-seed adapter bundles through the existing local registry."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "core"))
sys.path.insert(0, str(ROOT / "packages" / "publisher"))

from linkskills_publisher.registry import PublisherRegistry, publisher_db_path  # noqa: E402


ADAPTERS = (
    "awesome-design-presets",
    "emil-design-engineering",
    "google-workspace-operations",
    "hybrid-development-methods",
    "impeccable-design-system",
    "taste-design-exploration",
)


def digest_json(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return "sha256:" + hashlib.sha256(body).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    registry = PublisherRegistry(publisher_db_path(args.state_dir.resolve()))
    releases = []
    try:
        for skill_id in ADAPTERS:
            published = registry.publish_release(
                ROOT / "skills" / skill_id,
                channel="canary",
                metadata={
                    "consumer_activation": False,
                    "lifecycle_state": "eval_pending",
                    "ordinary_selectable": False,
                    "stable_qualified": False,
                },
            )
            releases.append(
                {
                    "bundle_hash": published.bundle_hash,
                    "channel": published.channel,
                    "release_hash": published.release_hash,
                    "skill_id": published.skill_id,
                    "version": published.version,
                }
            )
    finally:
        registry.close()

    receipt = {
        "consumer_activation": False,
        "current_pointer_changed": False,
        "kind": "initial-skill-seed-local-canary-publication",
        "live_provider_publication": False,
        "ordinary_selectability": False,
        "published_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "publisher": "linkskills-publisher-sqlite-registry",
        "releases": releases,
        "schema_version": "0.1",
        "stable_qualification": False,
    }
    receipt["receipt_digest"] = digest_json(receipt)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
