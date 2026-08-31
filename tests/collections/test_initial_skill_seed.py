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
sys.path.insert(0, str(ROOT / "packages" / "core"))

from linkskills_contracts import validate_instance  # noqa: E402
from linkskills_core.hashing import build_skill_bundle_manifest  # noqa: E402


COLLECTION_COUNTS = {
    "google-workspace": 95,
    "impeccable": 1,
    "taste-design": 13,
    "emil-design": 12,
    "awesome-design": 67,
    "hybrid-development": 19,
}

GOOGLE_WORKSPACE_QUARANTINE = set(
    json.loads(
        (ROOT / "collections" / "google-workspace" / "review.json").read_text()
    )["quarantine_candidates"]
)

ADAPTERS = {
    "google-workspace-operations": "google-workspace",
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
                decision = {
                    "taste-gpt-tasteskill": "needs_correction",
                    "taste-output-skill": "needs_correction",
                    "taste-taste-skill-v1": "superseded",
                }.get(
                    skill_id,
                    "needs_focused_review"
                    if collection_id == "google-workspace" and skill_id in GOOGLE_WORKSPACE_QUARANTINE
                    else "approved_internal_canary",
                )
                expected_lifecycle = "eval_pending" if decision == "approved_internal_canary" else ("superseded" if decision == "superseded" else "unqualified")
                self.assertEqual(release["lifecycle_state"], expected_lifecycle)
                self.assertEqual(eligibility["decision"], "ineligible")
                self.assertFalse(eligibility["consumer_profile_activation"]["status"])

    def test_vendor_inventory_and_release_digests_match_preserved_bytes(self) -> None:
        for collection_id in COLLECTION_COUNTS:
            if collection_id == "google-workspace":
                # This collection uses its original single-file artifact hash
                # convention and has a dedicated integrity test module.
                continue
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

    def test_non_admitted_members_are_rejected_before_source_disclosure(self) -> None:
        helper = ROOT / "skills" / "taste-design-exploration" / "scripts" / "helper_tool.py"
        for route_id, state in (
            ("taste-output-skill", "needs_correction"),
            ("taste-gpt-tasteskill", "needs_correction"),
            ("taste-taste-skill-v1", "superseded"),
        ):
            completed = subprocess.run(
                [sys.executable, str(helper), "--route-id", route_id],
                check=True,
                text=True,
                capture_output=True,
            )
            result = load_json(completed.stdout)
            self.assertEqual(result["status"], "NOT_ELIGIBLE")
            self.assertEqual(result["admission_state"], state)
            self.assertIsNone(result["source_entrypoint"])

        google_helper = ROOT / "skills" / "google-workspace-operations" / "scripts" / "helper_tool.py"
        for route_id in sorted(GOOGLE_WORKSPACE_QUARANTINE):
            completed = subprocess.run(
                [sys.executable, str(google_helper), "--route-id", route_id],
                check=True,
                text=True,
                capture_output=True,
            )
            result = load_json(completed.stdout)
            self.assertEqual(result["status"], "NOT_ELIGIBLE")
            self.assertEqual(result["admission_state"], "needs_focused_review")
            self.assertIsNone(result["source_entrypoint"])

    def test_activation_manifests_are_exact_and_consumer_owned(self) -> None:
        audit = load(ROOT / "evidence" / "initial-skill-seed" / "member-classification.json")
        self.assertEqual(audit["summary"]["total"], 207)
        self.assertEqual(
            audit["summary"]["counts"],
            {
                "approved_internal_canary": 182,
                "needs_correction": 2,
                "needs_focused_review": 22,
                "superseded": 1,
            },
        )
        approved = {item["release_id"] for item in audit["members"] if item["decision"] == "approved_internal_canary"}
        for path in sorted((ROOT / "configs" / "consumer-activation").glob("*-internal-canary.json")):
            manifest = load(path)
            self.assertEqual(manifest["activation"], {"activation_owner": "consumer", "enabled": False})
            self.assertFalse(manifest["live_apply"])
            self.assertFalse(manifest["stable_qualification_claimed"])
            self.assertTrue(set(manifest["permitted_release_ids"]) <= approved)
            for adapter in manifest["adapter_releases"]:
                bundle = build_skill_bundle_manifest(ROOT / "skills" / adapter["skill_id"])
                self.assertEqual(adapter["version"], bundle["version"])
                self.assertEqual(adapter["bundle_hash"], bundle["bundle_hash"])

    def test_generated_admission_artifacts_are_current(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "prepare_initial_canary_admission.py"), "--check"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_canary_publication_receipt_binds_exact_adapter_bundles(self) -> None:
        receipt = load(ROOT / "evidence" / "initial-skill-seed" / "canary-publication-receipt.json")
        self.assertEqual(len(receipt["releases"]), 6)
        self.assertFalse(receipt["consumer_activation"])
        self.assertFalse(receipt["current_pointer_changed"])
        self.assertFalse(receipt["live_provider_publication"])
        self.assertFalse(receipt["ordinary_selectability"])
        self.assertFalse(receipt["stable_qualification"])
        for release in receipt["releases"]:
            bundle = build_skill_bundle_manifest(ROOT / "skills" / release["skill_id"])
            self.assertEqual(release["bundle_hash"], bundle["bundle_hash"])
            self.assertEqual(release["release_hash"], bundle["bundle_hash"].removeprefix("sha256:"))

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
