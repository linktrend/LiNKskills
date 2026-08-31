#!/usr/bin/env python3
"""Integrity, contract, and non-overlap tests for the initial skill seed."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "contracts"))

from linkskills_contracts import validate_instance  # noqa: E402


COLLECTION_COUNTS = {
    "impeccable": 1,
    "taste-design": 13,
    "emil-design": 12,
    "awesome-design": 67,
    "hybrid-development": 19,
}

ADAPTERS = {
    "impeccable-design-system": "impeccable",
    "taste-design-exploration": "taste-design",
    "emil-design-engineering": "emil-design",
    "awesome-design-presets": "awesome-design",
    "hybrid-development-methods": "hybrid-development",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def digest_json(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return "sha256:" + hashlib.sha256(body).hexdigest()


class InitialSkillSeedTests(unittest.TestCase):
    def test_collection_contracts_counts_and_fail_closed_state(self) -> None:
        release_ids: set[str] = set()
        for collection_id, count in COLLECTION_COUNTS.items():
            collection = ROOT / "collections" / collection_id
            manifest = load(collection / "collection-manifest.json")
            result = validate_instance(manifest, "collection-manifest")
            self.assertTrue(result.ok, f"{collection_id}: {result.errors}")
            unsigned = {key: value for key, value in manifest.items() if key != "manifest_digest"}
            self.assertEqual(manifest["manifest_digest"], digest_json(unsigned))
            self.assertEqual(len(manifest["members"]), count)
            self.assertTrue(manifest["inactive_by_default"])
            self.assertEqual(manifest["lifecycle_state"], "eval_pending")

            role_pack = load(collection / "role-pack-manifest.json")
            role_result = validate_instance(role_pack, "role-pack-manifest")
            self.assertTrue(role_result.ok, f"{collection_id}: {role_result.errors}")
            self.assertEqual(role_pack["activation"], {"enabled": False, "activation_owner": "consumer"})

            for member in manifest["members"]:
                release_id = member["release_id"]
                self.assertNotIn(release_id, release_ids)
                release_ids.add(release_id)
                skill_id = member["skill_id"]
                release = load(collection / "releases" / f"{skill_id}.json")
                resource_id = member["resource_ids"][0]
                resource = load(collection / "resources" / f"{resource_id}.json")
                eligibility = load(collection / "eligibility" / f"{skill_id}-ineligible.json")
                for schema, payload in (
                    ("release-record", release),
                    ("exact-resource-descriptor", resource),
                    ("eligibility-metadata", eligibility),
                ):
                    validation = validate_instance(payload, schema)
                    self.assertTrue(validation.ok, f"{collection_id}/{skill_id}: {validation.errors}")
                self.assertEqual(release["lifecycle_state"], "unqualified")
                self.assertEqual(eligibility["decision"], "ineligible")
                self.assertFalse(eligibility["consumer_profile_activation"]["status"])

    def test_vendor_inventory_and_release_digests_match_preserved_bytes(self) -> None:
        for collection_id in COLLECTION_COUNTS:
            collection = ROOT / "collections" / collection_id
            manifest = load(collection / "collection-manifest.json")
            collection_entries = []
            for member in manifest["members"]:
                skill_id = member["skill_id"]
                release = load(collection / "releases" / f"{skill_id}.json")
                root = ROOT / "vendor-skills" / collection_id / skill_id
                entries = []
                for path in sorted(item for item in root.rglob("*") if item.is_file()):
                    body = path.read_bytes()
                    entry = {
                        "path": path.relative_to(root).as_posix(),
                        "digest": "sha256:" + hashlib.sha256(body).hexdigest(),
                        "size": len(body),
                    }
                    entries.append(entry)
                    collection_entries.append({"skill_id": skill_id, **entry})
                self.assertEqual(member["inventory_digest"], digest_json(entries))
                self.assertEqual(release["bundle_hash"], digest_json(entries))
                self.assertEqual(
                    member["content_digest"],
                    digest_json([{"path": item["path"], "digest": item["digest"]} for item in entries]),
                )
            self.assertEqual(manifest["inventory_digest"], digest_json(collection_entries))

    def test_adapters_reference_every_member_and_no_source_is_missing(self) -> None:
        for adapter, collection_id in ADAPTERS.items():
            adapter_root = ROOT / "skills" / adapter
            routing = load(adapter_root / "references" / "routing.json")
            manifest = load(ROOT / "collections" / collection_id / "collection-manifest.json")
            members = {item["skill_id"] for item in manifest["members"]}
            routed_members = {
                Path(item["source_entrypoint"]).parts[2] for item in routing["routes"]
            }
            self.assertEqual(routed_members, members)
            for route in routing["routes"]:
                self.assertTrue((ROOT / route["source_entrypoint"]).is_file(), route)

    def test_namespaces_prevent_known_collisions(self) -> None:
        awesome = load(ROOT / "collections" / "awesome-design" / "collection-manifest.json")
        taste = load(ROOT / "collections" / "taste-design" / "collection-manifest.json")
        self.assertIn("awesome-impeccable", {item["skill_id"] for item in awesome["members"]})
        self.assertNotIn("impeccable", {item["skill_id"] for item in awesome["members"]})
        self.assertTrue(all(item["skill_id"].startswith("taste-") for item in taste["members"]))

    def test_representative_routing_is_single_and_task_specific(self) -> None:
        probes = {
            "impeccable-design-system": ("polish the final pass", "polish"),
            "taste-design-exploration": ("create a brutalist exploration", "taste-brutalist-skill"),
            "emil-design-engineering": ("write modern Swift concurrency code", "emil-write-swift"),
            "awesome-design-presets": ("use the glassmorphism preset", "awesome-glassmorphism"),
            "hybrid-development-methods": ("use TDD for this fix", "mattpocock-tdd"),
        }
        for adapter, (task, expected) in probes.items():
            completed = subprocess.run(
                [sys.executable, str(ROOT / "skills" / adapter / "scripts" / "helper_tool.py"), "--route", task],
                check=True,
                text=True,
                capture_output=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(result["status"], "SELECTED", (adapter, result))
            self.assertEqual(result["selected_route"], expected, (adapter, result))

    def test_unknown_task_does_not_select_a_design_or_development_source(self) -> None:
        for adapter in ADAPTERS:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "skills" / adapter / "scripts" / "helper_tool.py"), "--route", "prepare a tax return"],
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertEqual(load_json(completed.stdout)["status"], "NOT_APPLICABLE")


def load_json(text: str) -> dict:
    return json.loads(text)


if __name__ == "__main__":
    unittest.main()
