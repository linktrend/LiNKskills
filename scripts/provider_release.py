#!/usr/bin/env python3
"""Qualify and publish five immutable releases; never activate a consumer."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path

from linkskills_eval_runner.ed03 import INITIAL_RELEASE_PROFILES, qualify_initial_release_profiles
from linkskills_gateway.production_v2 import decode_release, manifest_digest
from linkskills_publisher.initial_set import collect_skill_files


def canonical(value):
    """Return deterministic bytes for the external issuer signature."""
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def issuer_key():
    """Read issuer material from process environment only; never return it in evidence."""
    value = os.environ.get("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", "")
    if len(value.encode()) < 32:
        raise ValueError("issuer_material_missing_or_weak")
    return value.encode()


def export_package(root: Path, output: Path):
    """Execute the real suite and seal its outcome together with exact resource bytes."""
    matrix = qualify_initial_release_profiles(root, evidence_dir=output.parent / "cases")
    if len(matrix["usable"]) != 5 or matrix["evalPending"] or matrix["quarantined"]:
        output.with_suffix(".pending.json").write_text(json.dumps(matrix, indent=2) + "\n")
        raise ValueError("qualification_not_complete")
    source = json.loads((root / "source-identity.json").read_text())
    rows = []
    qualification_digest = manifest_digest(matrix)
    for spec in INITIAL_RELEASE_PROFILES:
        files = collect_skill_files(root / "skills" / spec["skillId"])
        resources = {}
        for name, body in sorted(files.items()):
            resource_id = "entrypoint" if name == "SKILL.md" else name
            resources[resource_id] = {
                "content_b64": base64.b64encode(body).decode(),
                "content_digest": "sha256:" + hashlib.sha256(body).hexdigest(),
                "resource_kind": "entrypoint" if name == "SKILL.md" else "section",
                "media_type": "text/markdown" if name.endswith(".md") else "application/octet-stream",
                "provenance": source,
                "licence": {"spdx": "LicenseRef-LiNKtrend-Internal"},
            }
        manifest = {
            "skill_id": spec["skillId"], "version": spec["version"],
            "family_id": "development", "qualification": "qualified",
            "runtime_profiles": [spec["runtimeProfile"]], "resources": resources,
            "platform_technical_eligibility": True, "skills_release_selectability": True,
            "consumer_profile_activation": True, "consumer_tool_authority": True,
            "provenance": source,
        }
        rows.append({"release_id": f"{spec['skillId']}@{spec['version']}",
                     "manifest": manifest, "manifest_sha256": manifest_digest(manifest),
                     "qualification_sha256": qualification_digest, "lifecycle": "qualified"})
    payload = {"schemaVersion": 1, "source": source, "qualification": matrix,
               "releases": rows, "consumerActivation": False}
    signature = hmac.new(issuer_key(), canonical(payload), hashlib.sha256).hexdigest()
    output.write_text(json.dumps({"payload": payload, "issuer_signature": signature}, sort_keys=True) + "\n")
    return {"qualified": 5, "published": False, "consumerActivation": False,
            "packageDigest": "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest()}


def import_package(path: Path, expected_commit: str):
    """Verify the issuer seal and insert idempotently using a publisher-only credential."""
    import psycopg
    from psycopg.types.json import Jsonb

    document = json.loads(path.read_text())
    payload = document["payload"]
    expected = hmac.new(issuer_key(), canonical(payload), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, document["issuer_signature"]):
        raise ValueError("package_signature_invalid")
    if payload["source"]["commit"] != expected_commit or payload.get("consumerActivation") is not False:
        raise ValueError("package_identity_mismatch")
    allowed = {f"{s['skillId']}@{s['version']}" for s in INITIAL_RELEASE_PROFILES}
    rows = payload["releases"]
    if len(rows) != 5 or {r["release_id"] for r in rows} != allowed:
        raise ValueError("initial_allowlist_mismatch")
    if len(payload["qualification"].get("usable", [])) != 5:
        raise ValueError("qualification_not_complete")
    for row in rows:
        decode_release(row)
        if row["qualification_sha256"] != manifest_digest(payload["qualification"]):
            raise ValueError("qualification_digest_mismatch")
    with psycopg.connect(os.environ["LINKSKILLS_PUBLISHER_DATABASE_URL"], connect_timeout=5) as conn:
        conn.execute("set local role svc_lskills_librarian")
        for row in rows:
            conn.execute(
                "insert into lskills.provider_releases "
                "(release_id,manifest,manifest_sha256,qualification_sha256) values (%s,%s,%s,%s) "
                "on conflict do nothing",
                (row["release_id"], Jsonb(row["manifest"]), row["manifest_sha256"], row["qualification_sha256"]),
            )
            existing = conn.execute(
                "select manifest_sha256, qualification_sha256, lifecycle from lskills.provider_releases where release_id=%s",
                (row["release_id"],),
            ).fetchone()
            if existing != (row["manifest_sha256"], row["qualification_sha256"], "qualified"):
                raise ValueError("immutable_publication_conflict")
    return {"published": 5, "consumerActivation": False, "source": payload["source"]}


def main():
    """Expose separate qualification and privileged publication commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("qualify", "publish"))
    parser.add_argument("--root", type=Path, default=Path("/opt/linkskills"))
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--expected-commit", default="")
    args = parser.parse_args()
    try:
        result = export_package(args.root, args.package) if args.command == "qualify" else import_package(args.package, args.expected_commit)
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        # DSNs, key values and database diagnostic text must never enter logs.
        print(json.dumps({"ok": False, "errorType": type(exc).__name__}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
