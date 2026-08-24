#!/usr/bin/env python3
"""PKT-01 provider taxonomy and release metadata contract tests."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "contracts"))

from linkskills_contracts import validate_instance  # noqa: E402


DIGEST = "sha256:" + ("a" * 64)
COMMIT = "a" * 40


def taxonomy() -> dict:
    return {
        "schema_version": "0.1",
        "taxonomy_id": "linkskills-catalogue",
        "taxonomy_version": "1.0.0",
        "owner": "linkskills",
        "trust_boundary": "linkskills-taxonomy",
        "families": [
            {
                "family_id": "research",
                "display_name": "Research",
                "description": "Source-grounded research methods.",
                "subcategories": [
                    {
                        "subcategory_id": "web-research",
                        "display_name": "Web Research",
                        "description": "Research using reviewed sources.",
                        "collections": [
                            {"collection_id": "shared-methods", "display_name": "Shared Methods", "description": "Reusable research methods."}
                        ],
                    }
                ],
            }
        ],
    }


def resource() -> dict:
    return {
        "schema_version": "0.1",
        "resource_id": "entrypoint",
        "release_id": "research@1.0.0",
        "skill_id": "research",
        "skill_version": "1.0.0",
        "resource_kind": "entrypoint",
        "resource_uri": "skills://release/research/1.0.0/entrypoint",
        "media_type": "text/markdown",
        "byte_size": 128,
        "content_digest": DIGEST,
        "immutable": True,
        "disclosure_level": 3,
        "provenance": {
            "source_kind": "native",
            "publisher": "LiNKskills",
            "repository": "https://github.com/linktrend/LiNKskills",
            "source_ref": "development",
            "source_commit": COMMIT,
            "source_path": "skills/research/SKILL.md",
            "retrieved_at": "2026-08-24T00:00:00Z",
        },
        "licence": {
            "licence_id": "LiNKtrend-proprietary",
            "attribution_required": False,
            "review_status": "not_required",
        },
        "trust_boundary": "linkskills-resource",
    }


def collection() -> dict:
    return {
        "schema_version": "0.1",
        "collection_id": "shared-methods",
        "version": "1.0.0",
        "display_name": "Shared Methods",
        "description": "Reviewed reusable methods.",
        "manifest_digest": DIGEST,
        "inventory_digest": DIGEST,
        "source": {
            "publisher": "LiNKskills",
            "repository": "https://github.com/linktrend/LiNKskills",
            "source_ref": "development",
            "source_commit": COMMIT,
            "retrieved_at": "2026-08-24T00:00:00Z",
            "licence": {
                "licence_id": "LiNKtrend-proprietary",
                "attribution_required": False,
                "review_status": "not_required",
            },
        },
        "members": [
            {
                "release_id": "research@1.0.0",
                "skill_id": "research",
                "version": "1.0.0",
                "release_kind": "native",
                "artifact_digest": DIGEST,
                "inventory_digest": DIGEST,
                "content_digest": DIGEST,
                "resource_ids": ["entrypoint"],
            }
        ],
        "lifecycle_state": "qualified",
        "inactive_by_default": True,
        "trust_boundary": "linkskills-collection",
    }


def eligibility() -> dict:
    gate = {"status": True, "evidence_ref": "opaque:evidence:1", "evaluated_by": "linkskills-validator"}
    return {
        "schema_version": "0.1",
        "eligibility_id": "research-1",
        "release_id": "research@1.0.0",
        "evaluated_at": "2026-08-24T00:00:00Z",
        "platform_technical_eligibility": gate,
        "skills_release_selectability": gate,
        "consumer_profile_activation": gate,
        "consumer_tool_authority": gate,
        "decision": "eligible",
        "trust_boundary": "linkskills-eligibility",
    }


def role_pack() -> dict:
    return {
        "schema_version": "0.1",
        "role_pack_id": "researcher",
        "version": "1.0.0",
        "display_name": "Researcher",
        "description": "Reference-only research release selection.",
        "release_refs": [{"release_id": "research@1.0.0", "artifact_digest": DIGEST, "eligibility_ref": "opaque:eligibility:research-1"}],
        "applicability": {
            "role_class": "researcher",
            "task_classes": ["source-review"],
            "scope": "general",
            "constraints": ["No private data."],
        },
        "required_capability_classes": ["web.read"],
        "compatibility": {"runtime_profiles": ["codex"], "min_contract_version": "0.2"},
        "activation": {"enabled": False, "activation_owner": "consumer"},
        "trust_boundary": "linkskills-role-pack",
    }


def update_candidate() -> dict:
    return {
        "schema_version": "0.1",
        "candidate_id": "google-cli-20260824",
        "idempotency_key": "candidate:google-cli:20260824",
        "submitted_at": "2026-08-24T00:00:00Z",
        "submitted_by": "linkautowork",
        "source": {
            "publisher": "Example Publisher",
            "repository": "https://github.com/example/source",
            "old_ref": "v1.0.0",
            "new_ref": "v1.1.0",
            "old_inventory_digest": DIGEST,
            "new_inventory_digest": DIGEST,
            "old_content_digest": DIGEST,
            "new_content_digest": DIGEST,
            "source_commit": COMMIT,
        },
        "diff": {"reference": "opaque:diff:20260824", "digest": DIGEST, "changed_resource_ids": ["entrypoint"]},
        "licence_finding": "unchanged_compatible",
        "review_state": "pending",
        "automatic_promotion": False,
        "current_pointer_change": False,
        "attestation": {
            "algorithm": "ES256",
            "key_id": "upstream-poller-key-1",
            "issuer": "linkskills-upstream-poller",
            "claims_digest": DIGEST,
            "signature": "signature-bytes",
            "trust_boundary": "linkskills-update-attestation",
        },
        "trust_boundary": "linkskills-update-candidate",
    }


def release_record() -> dict:
    return {
        "schema_version": "0.1",
        "release_id": "research@1.0.0",
        "artifact_kind": "skill_pack",
        "artifact_id": "research",
        "version": "1.0.0",
        "bundle_hash": DIGEST,
        "channel": "stable",
        "lifecycle_state": "qualified",
        "published_at": "2026-08-24T00:00:00Z",
        "release_kind": "native",
        "inventory_digest": DIGEST,
        "content_digest": DIGEST,
        "provenance": {
            "publisher": "LiNKskills",
            "repository": "https://github.com/linktrend/LiNKskills",
            "source_ref": "development",
            "source_commit": COMMIT,
            "source_path": "skills/research",
            "retrieved_at": "2026-08-24T00:00:00Z",
            "licence": "LiNKtrend-proprietary",
            "trust_boundary": "linkskills-release-provenance",
        },
        "lineage": {"kind": "native", "upstream_release_id": None, "relationship": "none"},
        "resource_descriptors": ["opaque:resource:research-entrypoint"],
        "eligibility_ref": "opaque:eligibility:research-1",
        "attestation": {
            "algorithm": "ES256",
            "key_id": "publisher-key-1",
            "issuer": "linkskills-publisher",
            "claims_digest": DIGEST,
            "signature": "signature-bytes",
            "trust_boundary": "linkskills-release-attestation",
        },
    }


class ProviderReleaseMetadataTests(unittest.TestCase):
    def assert_valid(self, payload: dict, schema: str) -> None:
        result = validate_instance(payload, schema)
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])

    def assert_invalid(self, payload: dict, schema: str) -> None:
        result = validate_instance(payload, schema)
        self.assertFalse(result.ok, msg=[str(error) for error in result.errors])

    def test_taxonomy_collection_resource_and_role_contracts(self) -> None:
        self.assert_valid(taxonomy(), "provider-taxonomy-v0.1.json")
        self.assert_valid(collection(), "collection-manifest-v0.1.json")
        self.assert_valid(resource(), "exact-resource-descriptor-v0.1.json")
        self.assert_valid(eligibility(), "eligibility-metadata-v0.1.json")
        self.assert_valid(role_pack(), "role-pack-manifest-v0.1.json")
        self.assert_valid(update_candidate(), "update-candidate-v0.1.json")
        self.assert_valid(release_record(), "release-record-v0.1.json")

    def test_unknown_trust_boundaries_fail_closed(self) -> None:
        for schema, payload, field in (
            ("provider-taxonomy-v0.1.json", taxonomy(), "trust_boundary"),
            ("collection-manifest-v0.1.json", collection(), "trust_boundary"),
            ("exact-resource-descriptor-v0.1.json", resource(), "trust_boundary"),
            ("eligibility-metadata-v0.1.json", eligibility(), "trust_boundary"),
            ("role-pack-manifest-v0.1.json", role_pack(), "trust_boundary"),
            ("update-candidate-v0.1.json", update_candidate(), "trust_boundary"),
        ):
            payload[field] = "unknown-boundary"
            self.assert_invalid(payload, schema)

    def test_incomplete_provenance_and_unknown_fields_fail_closed(self) -> None:
        missing_source_path = copy.deepcopy(resource())
        del missing_source_path["provenance"]["source_path"]
        self.assert_invalid(missing_source_path, "exact-resource-descriptor-v0.1.json")

        missing_release_provenance = {
            "schema_version": "0.1",
            "release_id": "research@1.0.0",
            "artifact_kind": "skill_pack",
            "artifact_id": "research",
            "version": "1.0.0",
            "bundle_hash": DIGEST,
            "channel": "stable",
            "lifecycle_state": "qualified",
            "published_at": "2026-08-24T00:00:00Z",
            "release_kind": "vendor",
        }
        self.assert_invalid(missing_release_provenance, "release-record-v0.1.json")

        unknown = copy.deepcopy(collection())
        unknown["vendor_taxonomy"] = "second-authority"
        self.assert_invalid(unknown, "collection-manifest-v0.1.json")

        mismatched_lineage = release_record()
        mismatched_lineage["release_kind"] = "adapted"
        mismatched_lineage["lineage"] = {"kind": "native", "upstream_release_id": None, "relationship": "none"}
        self.assert_invalid(mismatched_lineage, "release-record-v0.1.json")

    def test_eligibility_is_an_intersection_and_role_pack_cannot_activate(self) -> None:
        ineligible = eligibility()
        ineligible["decision"] = "eligible"
        ineligible["consumer_tool_authority"]["status"] = False
        self.assert_invalid(ineligible, "eligibility-metadata-v0.1.json")

        activated = role_pack()
        activated["activation"]["enabled"] = True
        self.assert_invalid(activated, "role-pack-manifest-v0.1.json")

    def test_candidate_cannot_promote_or_switch_current_pointer(self) -> None:
        candidate = update_candidate()
        candidate["automatic_promotion"] = True
        self.assert_invalid(candidate, "update-candidate-v0.1.json")

        candidate = update_candidate()
        candidate["current_pointer_change"] = True
        self.assert_invalid(candidate, "update-candidate-v0.1.json")


if __name__ == "__main__":
    unittest.main()
