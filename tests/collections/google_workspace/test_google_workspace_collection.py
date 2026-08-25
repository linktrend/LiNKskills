#!/usr/bin/env python3
"""PKT-05 Google Workspace collection admission and integrity checks."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "contracts"))

from linkskills_contracts import validate_instance  # noqa: E402


COLLECTION = ROOT / "collections" / "google-workspace"
VENDOR = ROOT / "vendor-skills" / "google-workspace"
COMMIT = "a3768d0e82ad83cca2da97724e46bea4ff0e6dbd"
TREE = "28127e4c0edff4bdf9226369e7a2ef744b353c25"
INVENTORY_DIGEST = "sha256:b33e2a377eab6cdaa85740d47c0a378e5ab29740aaea5a5b1aec3c926e58e696"
CONTENT_DIGEST = "sha256:b0b62ebb00bc2e1253a0b060bdd2bb7c41b188531bba8076562f6b5f63310ce6"
MANIFEST_DIGEST = "sha256:396365c352a04ae962eabd3044fe6e8cafc4d6bd306e10e6c7ca0311928dc716"
DIGEST_RE = re.compile(r"^sha256:[a-f0-9]{64}$")


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_json(value: object) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())


def load(path: Path) -> dict:
    return json.loads(path.read_text())


class GoogleWorkspaceCollectionTests(unittest.TestCase):
    def test_inventory_is_complete_and_manifest_digest_recomputes(self) -> None:
        manifest = load(COLLECTION / "collection-manifest.json")
        skills = sorted(p.parent.name for p in VENDOR.glob("*/SKILL.md"))
        self.assertEqual(len(skills), 95)
        self.assertEqual(len(manifest["members"]), 95)
        self.assertEqual(manifest["source"]["source_commit"], COMMIT)
        self.assertEqual(manifest["inventory_digest"], INVENTORY_DIGEST)
        self.assertEqual(manifest["manifest_digest"], MANIFEST_DIGEST)
        unsigned = {key: value for key, value in manifest.items() if key != "manifest_digest"}
        self.assertEqual(digest_json(unsigned), MANIFEST_DIGEST)
        self.assertTrue(manifest["inactive_by_default"])
        self.assertEqual(manifest["lifecycle_state"], "unqualified")
        self.assertEqual(manifest["trust_boundary"], "linkskills-collection")

        entries = []
        for skill in skills:
            body = (VENDOR / skill / "SKILL.md").read_bytes()
            entries.append({"path": f"skills/{skill}/SKILL.md", "digest": digest_bytes(body), "size": len(body)})
        self.assertEqual(digest_json(entries), INVENTORY_DIGEST)
        self.assertEqual(digest_json([{"path": entry["path"], "digest": entry["digest"]} for entry in entries]), CONTENT_DIGEST)

    def test_every_vendor_release_resource_and_eligibility_is_contract_valid(self) -> None:
        for schema, path in (
            ("collection-manifest", COLLECTION / "collection-manifest.json"),
            ("role-pack-manifest", COLLECTION / "role-pack-manifest.json"),
            ("update-candidate", COLLECTION / "update-candidate.json"),
        ):
            result = validate_instance(load(path), schema)
            self.assertTrue(result.ok, f"{path}: {result.errors}")
        for path in sorted((COLLECTION / "releases").glob("*.json")):
            result = validate_instance(load(path), "release-record")
            self.assertTrue(result.ok, f"{path}: {result.errors}")
        for path in sorted((COLLECTION / "resources").glob("*.json")):
            result = validate_instance(load(path), "exact-resource-descriptor")
            self.assertTrue(result.ok, f"{path}: {result.errors}")
        for path in sorted((COLLECTION / "eligibility").glob("*.json")):
            result = validate_instance(load(path), "eligibility-metadata")
            self.assertTrue(result.ok, f"{path}: {result.errors}")

        self.assertEqual(len(list((COLLECTION / "releases").glob("*.json"))), 95)
        self.assertEqual(len(list((COLLECTION / "resources").glob("*.json"))), 95)
        self.assertEqual(len(list((COLLECTION / "eligibility").glob("*.json"))), 95)

    def test_release_lineage_and_per_resource_digests_match_preserved_bytes(self) -> None:
        manifest = load(COLLECTION / "collection-manifest.json")
        for member in manifest["members"]:
            skill = member["skill_id"]
            body = (VENDOR / skill / "SKILL.md").read_bytes()
            digest = digest_bytes(body)
            release = load(COLLECTION / "releases" / f"{skill}.json")
            resource = load(COLLECTION / "resources" / f"{skill}-skill-md.json")
            eligibility = load(COLLECTION / "eligibility" / f"{skill}-ineligible.json")
            self.assertEqual(member["release_kind"], "vendor")
            self.assertEqual(member["content_digest"], digest)
            self.assertEqual(member["artifact_digest"], digest)
            self.assertEqual(release["lineage"], {"kind": "vendor", "relationship": "preserved_vendor_bytes", "upstream_release_id": None})
            self.assertEqual(release["provenance"]["source_commit"], COMMIT)
            self.assertEqual(release["provenance"]["source_path"], f"skills/{skill}/SKILL.md")
            self.assertEqual(resource["content_digest"], digest)
            self.assertTrue(resource["immutable"])
            self.assertEqual(resource["provenance"]["source_commit"], COMMIT)
            self.assertEqual(eligibility["decision"], "ineligible")
            self.assertFalse(eligibility["consumer_profile_activation"]["status"])
            self.assertFalse(eligibility["consumer_tool_authority"]["status"])

    def test_lisa_role_pack_is_reference_only_and_update_cannot_promote(self) -> None:
        role = load(COLLECTION / "role-pack-manifest.json")
        self.assertFalse(role["activation"]["enabled"])
        self.assertEqual(role["activation"]["activation_owner"], "consumer")
        self.assertEqual({item["release_id"].split("@")[0] for item in role["release_refs"]}, {"gws-drive", "gws-docs", "gws-sheets", "gws-slides", "gws-gmail", "gws-calendar", "gws-tasks"})
        candidate = load(COLLECTION / "update-candidate.json")
        self.assertFalse(candidate["automatic_promotion"])
        self.assertFalse(candidate["current_pointer_change"])
        self.assertEqual(candidate["source"]["source_commit"], COMMIT)

    def test_vendor_bytes_have_no_secrets_or_private_destinations(self) -> None:
        forbidden = re.compile(r"(?:AIza[0-9A-Za-z_-]{20,}|ya29\.[0-9A-Za-z_-]+|BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY|(?:password|client_secret|access_token)\s*[:=]|/(?:Users|home|private/tmp)/)", re.IGNORECASE)
        email = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", re.IGNORECASE)
        synthetic_domains = {"example.com", "company.com", "service.com", "school.edu"}
        for path in VENDOR.glob("*/SKILL.md"):
            self.assertIsNone(forbidden.search(path.read_text()), path)
            self.assertTrue({match.group(1).lower() for match in email.finditer(path.read_text())} <= synthetic_domains, path)


if __name__ == "__main__":
    unittest.main()
