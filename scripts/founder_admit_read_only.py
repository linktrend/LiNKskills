#!/usr/bin/env python3
"""Build and publish explicitly founder-admitted, resource-read-only Skill Packs."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
from pathlib import Path


APPROVAL = {
    "decision": "founder_approved",
    "scope": "resource_read_only",
    "evaluation": "not_performed",
    "authority": "Carlos",
    "approved_on": "2026-10-06",
}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".csv"}
MAX_RESOURCE_BYTES = 1_000_000


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def build(source_root: Path, output: Path) -> dict[str, object]:
    """Seal the exact 63 source directories as non-qualified immutable resources."""
    releases = []
    source_hashes = {}
    for group in ("hormozi", "complementary"):
        group_root = source_root / group
        for pack in sorted(group_root.iterdir()):
            if not pack.is_dir() or not (pack / "SKILL.md").is_file():
                continue
            resources = []
            pack_hashes = []
            for path in sorted(pack.rglob("*")):
                if path.is_symlink() or not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                relative = path.relative_to(pack).as_posix()
                top_level = path.relative_to(pack).parts[0]
                if relative != "SKILL.md" and top_level not in {"advanced", "references", "examples"}:
                    continue
                body = path.read_bytes()
                if not body or len(body) > MAX_RESOURCE_BYTES:
                    raise ValueError(f"invalid_resource_size:{pack.name}:{relative}")
                resource_id = "entrypoint" if relative == "SKILL.md" else relative
                content_digest = digest(body)
                pack_hashes.append({"path": relative, "digest": content_digest, "bytes": len(body)})
                resources.append({
                    "resource_id": resource_id,
                    "resource_kind": "entrypoint" if relative == "SKILL.md" else "section",
                    "media_type": mimetypes.guess_type(relative)[0] or "text/plain",
                    "content_digest": content_digest,
                    "byte_size": len(body),
                    "content_b64": base64.b64encode(body).decode("ascii"),
                    "provenance": {"source_group": group, "source_path": str((Path(group) / pack.name / relative))},
                })
            if not any(row["resource_id"] == "entrypoint" for row in resources):
                raise ValueError(f"entrypoint_missing:{pack.name}")
            skill_id = pack.name
            release_id = f"{skill_id}@1.0.0"
            source_hash = digest(canonical(pack_hashes))
            source_hashes[release_id] = source_hash
            manifest = {
                "skill_id": skill_id,
                "version": "1.0.0",
                "family_id": "founder-admitted",
                "qualification": "founder_admitted_read_only",
                "lifecycle_state": "founder_admitted_read_only",
                "runtime_profiles": ["cursor-macos"],
                "resources": {
                    row["resource_id"]: {k: row[k] for k in (
                        "resource_kind", "media_type", "content_digest", "byte_size", "content_b64", "provenance"
                    )}
                    for row in resources
                },
                "platform_technical_eligibility": False,
                "skills_release_selectability": False,
                "consumer_profile_activation": False,
                "consumer_tool_authority": False,
                "provenance": {"source_group": group, "source_path": str(Path(group) / pack.name), "source_digest": source_hash},
                "founder_admission": {**APPROVAL, "source_digest": source_hash},
            }
            manifest_sha = digest(canonical(manifest))
            releases.append({
                "release_id": release_id,
                "manifest": manifest,
                "manifest_sha256": manifest_sha,
                "qualification_sha256": None,
                "lifecycle": "founder_admitted_read_only",
            })
    if len(releases) != 63:
        raise ValueError(f"expected_63_source_packs:{len(releases)}")
    payload = {
        "schemaVersion": 1,
        "admission": APPROVAL,
        "evaluation": "not_performed",
        "source_root": str(source_root),
        "releases": releases,
        "consumerActivation": False,
        "qualification": "not_claimed",
        "source_manifest_sha256": digest(canonical(source_hashes)),
    }
    output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {"release_count": len(releases), "source_manifest_sha256": payload["source_manifest_sha256"]}


def publish(package_path: Path) -> dict[str, object]:
    """Insert exact manifests/resources atomically using a publisher-only DB URL."""
    import os
    import psycopg
    from psycopg.types.json import Jsonb

    payload = json.loads(package_path.read_text(encoding="utf-8"))
    if payload.get("admission") != APPROVAL or payload.get("evaluation") != "not_performed":
        raise ValueError("founder_admission_record_invalid")
    rows = payload.get("releases")
    if not isinstance(rows, list) or len(rows) != 63:
        raise ValueError("expected_63_releases")
    source_hashes = {
        row["release_id"]: row["manifest"]["provenance"]["source_digest"]
        for row in rows
    }
    if digest(canonical(source_hashes)) != payload.get("source_manifest_sha256"):
        raise ValueError("source_manifest_digest_mismatch")
    dsn = os.environ.get("LINKSKILLS_PUBLISHER_DATABASE_URL")
    if not dsn:
        raise ValueError("publisher_database_url_missing")
    with psycopg.connect(dsn, connect_timeout=5) as conn:
        with conn.transaction():
            conn.execute("set local role svc_lskills_librarian")
            for row in rows:
                manifest = row["manifest"]
                if digest(canonical(manifest)) != row["manifest_sha256"]:
                    raise ValueError("manifest_digest_mismatch")
                if row["qualification_sha256"] is not None or row["lifecycle"] != "founder_admitted_read_only":
                    raise ValueError("qualification_state_mismatch")
                conn.execute(
                    "insert into lskills.provider_releases "
                    "(release_id,manifest,manifest_sha256,qualification_sha256,lifecycle) "
                    "values (%s,%s,%s,null,'founder_admitted_read_only') on conflict do nothing",
                    (row["release_id"], Jsonb(manifest), row["manifest_sha256"]),
                )
                existing = conn.execute(
                    "select manifest_sha256,qualification_sha256,lifecycle from lskills.provider_releases where release_id=%s",
                    (row["release_id"],),
                ).fetchone()
                if existing != (row["manifest_sha256"], None, "founder_admitted_read_only"):
                    raise ValueError("immutable_publication_conflict")
                for resource in manifest["resources"].values():
                    body = base64.b64decode(resource["content_b64"], validate=True)
                    if digest(body) != resource["content_digest"] or len(body) != resource["byte_size"]:
                        raise ValueError("resource_digest_mismatch")
    return {"published_count": len(rows), "qualification": "not_claimed", "evaluation": "not_performed"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "publish"))
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source_root, args.package) if args.command == "build" and args.source_root else publish(args.package) if args.command == "publish" else None
    if result is None:
        raise SystemExit("source_root_required_for_build")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
