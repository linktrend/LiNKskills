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
from linkskills_eval_runner.remainder import (
    UNPUBLISHED_SKILL_IDS,
    qualify_hosted_remainder_release_profiles,
)
from linkskills_gateway.production_v2 import decode_release, manifest_digest
from linkskills_publisher.initial_set import collect_skill_files

INITIAL_RELEASE_IDS = {f"{spec['skillId']}@{spec['version']}" for spec in INITIAL_RELEASE_PROFILES}


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
    allowed = set(INITIAL_RELEASE_IDS)
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


def _sealed_remainder_rows(matrix: dict) -> list[dict]:
    """Keep only hosted rows with issuer-sealed, isolation-denied receipts."""
    sealed = []
    unpublished = set(UNPUBLISHED_SKILL_IDS)
    for row in matrix.get("combinations") or []:
        skill_id = str(row.get("skillId") or "")
        if skill_id in unpublished:
            continue
        release_id = f"{skill_id}@{row.get('version')}"
        if release_id in INITIAL_RELEASE_IDS:
            continue
        run = row.get("run") or {}
        isolations = list(run.get("networkIsolation") or [])
        if (
            row.get("lifecycle") == "usable"
            and row["id"] in (matrix.get("usable") or [])
            and run.get("certified")
            and run.get("receiptHashes")
            and isolations
            and all(item == "denied" for item in isolations)
        ):
            sealed.append(row)
    return sealed


def _release_document(root: Path, spec: dict, source: dict, qualification_digest: str) -> dict:
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
        "skill_id": spec["skillId"],
        "version": spec["version"],
        "family_id": "shared-floor",
        "qualification": "qualified",
        "runtime_profiles": [spec["runtimeProfile"]],
        "resources": resources,
        "platform_technical_eligibility": True,
        "skills_release_selectability": True,
        "consumer_profile_activation": True,
        "consumer_tool_authority": True,
        "provenance": source,
    }
    return {
        "release_id": f"{spec['skillId']}@{spec['version']}",
        "manifest": manifest,
        "manifest_sha256": manifest_digest(manifest),
        "qualification_sha256": qualification_digest,
        "lifecycle": "qualified",
    }


def export_remainder_package(root: Path, output: Path):
    """Qualify shared-floor remainder ids on the hosted evaluator; seal receipts only."""
    matrix = qualify_hosted_remainder_release_profiles(root, evidence_dir=output.parent / "remainder-cases")
    sealed_rows = _sealed_remainder_rows(matrix)
    if not sealed_rows:
        output.with_suffix(".pending.json").write_text(json.dumps(matrix, indent=2) + "\n")
        raise ValueError("remainder_qualification_not_complete")
    source = json.loads((root / "source-identity.json").read_text())
    qualification_digest = manifest_digest(matrix)
    rows = [
        _release_document(
            root,
            {
                "skillId": row["skillId"],
                "version": row["version"],
                "runtimeProfile": row["runtimeProfile"],
            },
            source,
            qualification_digest,
        )
        for row in sealed_rows
    ]
    payload = {
        "schemaVersion": 1,
        "kind": "remainder-hosted-sealed-package",
        "source": source,
        "qualification": matrix,
        "releases": rows,
        "consumerActivation": False,
        "unpublished": sorted(UNPUBLISHED_SKILL_IDS),
    }
    signature = hmac.new(issuer_key(), canonical(payload), hashlib.sha256).hexdigest()
    output.write_text(json.dumps({"payload": payload, "issuer_signature": signature}, sort_keys=True) + "\n")
    return {
        "qualified": len(rows),
        "failed": len(matrix.get("evalPending") or []) + len(matrix.get("quarantined") or []),
        "unpublished": sorted(UNPUBLISHED_SKILL_IDS),
        "published": False,
        "consumerActivation": False,
        "packageDigest": "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest(),
        "releaseIds": [row["release_id"] for row in rows],
    }


def import_remainder_package(path: Path, expected_commit: str):
    """Publish only remainder ids that carry issuer-sealed hosted receipts."""
    import psycopg
    from psycopg.types.json import Jsonb

    document = json.loads(path.read_text())
    payload = document["payload"]
    expected = hmac.new(issuer_key(), canonical(payload), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, document["issuer_signature"]):
        raise ValueError("package_signature_invalid")
    if payload["source"]["commit"] != expected_commit or payload.get("consumerActivation") is not False:
        raise ValueError("package_identity_mismatch")
    if payload.get("kind") != "remainder-hosted-sealed-package":
        raise ValueError("remainder_package_kind_mismatch")
    rows = payload["releases"]
    release_ids = {r["release_id"] for r in rows}
    unpublished_hits = {
        r["release_id"]
        for r in rows
        if str(r["release_id"]).split("@", 1)[0] in UNPUBLISHED_SKILL_IDS
    }
    if unpublished_hits:
        raise ValueError("unpublished_skill_forbidden")
    if release_ids & INITIAL_RELEASE_IDS:
        raise ValueError("initial_release_in_remainder_package")
    usable = set(payload["qualification"].get("usable") or [])
    sealed_ids = {f"{row['skillId']}@{row['version']}" for row in _sealed_remainder_rows(payload["qualification"])}
    packaged_ids = {r["release_id"] for r in rows}
    if not packaged_ids or packaged_ids != sealed_ids:
        raise ValueError("remainder_sealed_set_mismatch")
    usable_release_ids = {combo.split("/", 1)[0] for combo in usable}
    if packaged_ids - usable_release_ids:
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
    return {
        "published": len(rows),
        "consumerActivation": False,
        "source": payload["source"],
        "releaseIds": sorted(packaged_ids),
        "unpublished": sorted(UNPUBLISHED_SKILL_IDS),
    }


def main():
    """Expose separate qualification and privileged publication commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("qualify", "publish", "qualify-remainder", "publish-remainder"),
    )
    parser.add_argument("--root", type=Path, default=Path("/opt/linkskills"))
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--expected-commit", default="")
    args = parser.parse_args()
    try:
        if args.command == "qualify":
            result = export_package(args.root, args.package)
        elif args.command == "publish":
            result = import_package(args.package, args.expected_commit)
        elif args.command == "qualify-remainder":
            result = export_remainder_package(args.root, args.package)
        else:
            result = import_remainder_package(args.package, args.expected_commit)
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        # DSNs, key values and database diagnostic text must never enter logs.
        print(json.dumps({"ok": False, "errorType": type(exc).__name__}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
