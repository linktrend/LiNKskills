#!/usr/bin/env python3
"""ED-04 source-only initial publication and selectability proofs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "publisher"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))

from linkskills_publisher.initial_set import (  # noqa: E402
    INITIAL_ALLOWLIST,
    ORDINARY_SELECTABLE_COUNT,
    PublicationError,
    SourceOnlyInitialPublisher,
    catalog_skill_count,
    publish_exact_initial_releases,
)


def _ed03_matrix(*, quarantined: str | None = None) -> dict:
    rows = []
    for spec in INITIAL_ALLOWLIST:
        lifecycle = "quarantined" if quarantined == spec.combination_id else "eval_pending"
        rows.append(
            {
                "id": spec.combination_id,
                "skillId": spec.skill_id,
                "version": spec.version,
                "runtimeProfile": spec.runtime_profile,
                "lifecycle": lifecycle,
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "initial-release-profile-matrix",
        "complete": True,
        "combinations": rows,
        "usable": [],
        "evalPending": [row["id"] for row in rows if row["lifecycle"] == "eval_pending"],
        "quarantined": [row["id"] for row in rows if row["lifecycle"] == "quarantined"],
    }


class InitialSetPublicationTests(unittest.TestCase):
    def test_allowlist_is_exactly_the_five_frozen_releases(self) -> None:
        self.assertEqual(len(INITIAL_ALLOWLIST), 5)
        self.assertEqual(ORDINARY_SELECTABLE_COUNT, 5)
        self.assertEqual(
            [item.release_id for item in INITIAL_ALLOWLIST],
            [
                "git-safeguard@1.1.0",
                "persistent-qa@1.0.0",
                "repository-manager@1.0.0",
                "skill-template@1.2.0",
                "tool-architect@1.0.0",
            ],
        )

    def test_exact_version_and_digest_retrieval_from_source(self) -> None:
        publisher, receipt = publish_exact_initial_releases(
            REPO_ROOT,
            qualification_matrix=_ed03_matrix(),
        )
        self.assertFalse(receipt["liveProviderMutation"])
        self.assertFalse(receipt["consumerConfiguration"])
        self.assertFalse(receipt["externalApply"])
        self.assertEqual(receipt["selectableCount"], 5)
        catalog_count = catalog_skill_count(REPO_ROOT)
        self.assertGreater(catalog_count, 5)
        self.assertNotEqual(receipt["selectableCount"], catalog_count)
        for spec in INITIAL_ALLOWLIST:
            by_version = publisher.retrieve_exact(spec.skill_id, spec.version)
            again = publisher.retrieve_exact(
                spec.skill_id,
                spec.version,
                digest=by_version["filesDigest"],
            )
            self.assertEqual(again["bundleDigest"], by_version["bundleDigest"])
            self.assertEqual(again["evalDigest"], by_version["evalDigest"])
            self.assertTrue(again["platformTechnicalEligibility"]["status"])
            self.assertTrue(again["skillsReleaseSelectability"]["status"])
            self.assertFalse(again["consumerProfileActivation"]["status"])
            with self.assertRaises(PublicationError):
                publisher.retrieve_exact(spec.skill_id, "latest")
            with self.assertRaises(PublicationError):
                publisher.retrieve_exact(
                    spec.skill_id,
                    spec.version,
                    digest="sha256:deadbeef",
                )

    def test_ineligible_profiles_are_denied_and_do_not_change_count(self) -> None:
        publisher, _receipt = publish_exact_initial_releases(
            REPO_ROOT,
            qualification_matrix=_ed03_matrix(),
        )
        denials = publisher.denial_matrix(
            [
                {
                    "skillId": "git-safeguard",
                    "version": "1.1.0",
                    "runtimeProfile": "codex-linux",
                },
                {
                    "skillId": "git-safeguard",
                    "version": "0.0.1",
                    "runtimeProfile": "cursor-macos",
                },
                {
                    "skillId": "agentsetup",
                    "version": "1.3.0",
                    "runtimeProfile": "cursor-macos",
                },
                {
                    "skillId": "audit-protocol",
                    "version": "1.0.0",
                    "runtimeProfile": "cursor-macos",
                },
            ]
        )
        self.assertEqual(len(denials), 4)
        self.assertTrue(all(row["denied"] for row in denials))
        self.assertIn("incompatible", denials[0]["reasons"])
        self.assertIn("release_not_selectable", denials[1]["reasons"])
        self.assertIn("release_not_selectable", denials[2]["reasons"])
        allowed = publisher.evaluate_request(
            skill_id="skill-template",
            version="1.2.0",
            runtime_profile="cursor-macos",
        )
        self.assertFalse(allowed["denied"])
        self.assertEqual(publisher.ordinary_selectable_count(), 5)

    def test_quarantined_combination_cannot_publish(self) -> None:
        quarantined = INITIAL_ALLOWLIST[1].combination_id
        publisher = SourceOnlyInitialPublisher()
        with self.assertRaises(PublicationError) as ctx:
            publisher.publish_initial_set(
                REPO_ROOT,
                qualification_matrix=_ed03_matrix(quarantined=quarantined),
            )
        self.assertIn("quarantined", str(ctx.exception))

    def test_idempotent_republish_and_pointer_rollback_after_revoke(self) -> None:
        publisher, first = publish_exact_initial_releases(
            REPO_ROOT,
            qualification_matrix=_ed03_matrix(),
        )
        second = publisher.publish_initial_set(
            REPO_ROOT,
            qualification_matrix=_ed03_matrix(),
            catalog_skill_count=catalog_skill_count(REPO_ROOT),
        )
        self.assertEqual(first["receiptDigest"], second["receiptDigest"])
        git_sg = publisher.retrieve_exact("git-safeguard", "1.1.0")
        publisher.revoke("git-safeguard", "1.1.0")
        with self.assertRaises(PublicationError):
            publisher.retrieve_exact("git-safeguard", "1.1.0")
        self.assertEqual(publisher.ordinary_selectable_count(), 4)
        denied = publisher.evaluate_request(
            skill_id="git-safeguard",
            version="1.1.0",
            runtime_profile="cursor-macos",
        )
        self.assertTrue(denied["denied"])
        self.assertIn("withdrawn", denied["reasons"])
        self.assertNotEqual(publisher.intended_pointers().get("git-safeguard"), "1.1.0")
        publisher.reinstate("git-safeguard", "1.1.0")
        publisher.rollback_pointer("git-safeguard", expected=None, version="1.1.0")
        restored = publisher.retrieve_exact("git-safeguard", "1.1.0")
        self.assertEqual(restored["filesDigest"], git_sg["filesDigest"])
        self.assertEqual(publisher.intended_pointers()["git-safeguard"], "1.1.0")

    def test_three_gates_are_independent(self) -> None:
        publisher, _receipt = publish_exact_initial_releases(
            REPO_ROOT,
            qualification_matrix=_ed03_matrix(),
        )
        record = publisher.retrieve_exact("tool-architect", "1.0.0")
        self.assertTrue(record["platformTechnicalEligibility"]["status"])
        self.assertTrue(record["skillsReleaseSelectability"]["status"])
        self.assertFalse(record["consumerProfileActivation"]["status"])
        self.assertEqual(publisher.ordinary_selectable_count(), 5)
        publisher.revoke("tool-architect", "1.0.0")
        stored = publisher._records["tool-architect@1.0.0"]
        self.assertTrue(stored["platformTechnicalEligibility"]["status"])
        self.assertFalse(stored["skillsReleaseSelectability"]["status"])
        self.assertFalse(stored["consumerProfileActivation"]["status"])
        self.assertEqual(publisher.ordinary_selectable_count(), 4)


if __name__ == "__main__":
    unittest.main()
