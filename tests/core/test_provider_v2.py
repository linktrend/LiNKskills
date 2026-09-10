#!/usr/bin/env python3
"""Adversarial production skills.api.v0.2 domain tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "persistence"))

from linkskills_core.provider_v2 import (  # noqa: E402
    InMemoryProviderStore,
    TrustedIdentity,
    V2Provider,
)


def _identity(**overrides):
    values = dict(
        org_id="org-a",
        actor_id="actor-a",
        audience="lskills-api",
        capabilities=frozenset({"skills.read", "skills.feedback"}),
        binding="runtime-binding",
        roles=frozenset({"researcher"}),
        runtime_profiles=frozenset({"codex-macos"}),
        activated_release_ids=frozenset({"research@1.0.0"}),
    )
    values.update(overrides)
    return TrustedIdentity(**values)


RELEASE = {
    "skill_id": "research",
    "version": "1.0.0",
    "family_id": "research",
    "lifecycle_state": "qualified",
    "qualification": "qualified",
    "roles": ["researcher"],
    "runtime_profiles": ["codex-macos"],
    "resources": {
        "entrypoint": {"body": b"exact instructions", "resource_kind": "entrypoint"},
        "overview": {"body": b"section-one", "resource_kind": "section"},
        "blob": {"body": b"pkg-bytes", "resource_kind": "content"},
    },
}


class ProviderV2DomainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemoryProviderStore()
        self.provider = V2Provider(
            lambda _: _identity(),
            families=[
                {"family_id": "research", "display_name": "Research", "description": "R"},
                {"family_id": "engineering", "display_name": "Engineering", "description": "E"},
            ],
            releases=[RELEASE],
            store=self.store,
        )
        self.base = {"protocol_version": "2026-07-28", "authorization": "trusted"}

    def call(self, operation: str, **extra):
        return self.provider.handle(dict(self.base, operation=operation, **extra))

    def test_wrong_protocol_and_session_fail_closed(self) -> None:
        self.assertEqual(
            self.provider.handle(dict(self.base, operation="skills_catalog_list", protocol_version="2024-11-05"))[
                "error"
            ],
            "contract_incompatible",
        )
        self.assertEqual(
            self.provider.handle(dict(self.base, operation="skills_catalog_list", session_id="x"))["error"],
            "session_not_supported",
        )

    def test_legacy_execution_has_no_provider_route(self) -> None:
        for operation in (
            "skills_run_start",
            "skills_run_update",
            "skills_run_complete",
            "skills_run_fail",
            "skills_tool_invoke",
            "skills_tool_resolve",
        ):
            self.assertEqual(self.call(operation)["error"], "legacy_execution_disabled")

    def test_cursor_tampering_and_wrong_snapshot_fail_closed(self) -> None:
        page = self.call("skills_catalog_list", limit=1)
        self.assertTrue(page["has_more"])
        self.assertEqual(
            self.call("skills_catalog_list", limit=1, cursor="snapshot:deadbeefdeadbeef:1")["error"],
            "cursor_snapshot_mismatch",
        )
        self.assertEqual(
            self.call("skills_catalog_list", limit=1, cursor=page["snapshot_id"] + ":not-an-int")["error"],
            "cursor_invalid",
        )

    def test_unqualified_inactive_revoked_expired_fail_closed(self) -> None:
        for extra, expected in (
            ({"qualification": "eval_pending"}, "not_qualified"),
            ({"skills_release_selectability": False}, "skills_release_selectability"),
            ({"lifecycle_state": "revoked"}, "revoked_release"),
            ({"lifecycle_state": "expired"}, "expired_release"),
        ):
            release = dict(RELEASE, **extra)
            provider = V2Provider(lambda _: _identity(), releases=[release], store=self.store)
            self.assertEqual(
                provider.handle(
                    dict(self.base, operation="skills_release_describe", skill_id="research", version="1.0.0")
                )["error"],
                expected,
            )

    def test_wrong_release_identity_and_digest(self) -> None:
        self.assertEqual(
            self.call("skills_release_describe", skill_id="research", version="9.9.9")["error"],
            "not_found",
        )
        self.assertEqual(
            self.call(
                "skills_release_resource_get",
                skill_id="research",
                version="1.0.0",
                resource_id="entrypoint",
                expected_digest="sha256:" + "0" * 64,
            )["error"],
            "integrity_mismatch",
        )
        exact = self.call(
            "skills_release_resource_get",
            skill_id="research",
            version="1.0.0",
            resource_id="entrypoint",
        )
        self.assertEqual(exact["bytes"], b"exact instructions")
        package = self.call("skills_release_package_get", skill_id="research", version="1.0.0")
        self.assertTrue(package["content_digest"].startswith("sha256:"))
        section = self.call(
            "skills_release_section_get",
            skill_id="research",
            version="1.0.0",
            section_id="overview",
        )
        self.assertEqual(section["bytes"], b"section-one")
        content = self.call(
            "skills_release_content_get",
            skill_id="research",
            version="1.0.0",
            content_id="blob",
        )
        self.assertEqual(content["bytes"], b"pkg-bytes")

    def test_release_history_and_verify(self) -> None:
        history = self.call("skills_release_list", skill_id="research")
        self.assertEqual(history["items"][0]["release_id"], "research@1.0.0")
        verified = self.call("skills_release_verify", skill_id="research", version="1.0.0")
        self.assertTrue(verified["verified"])

    def test_use_feedback_idempotency_and_privacy(self) -> None:
        report = {
            "schema_version": "0.2",
            "report_kind": "completed_use",
            "report_id": "opaque:report:10",
            "occurred_at": "2026-08-13T00:00:00Z",
            "skill_id": "research",
            "skill_release_ref": "opaque:release:research:1.0.0",
            "consumer_class": "codex",
            "actor_ref": "opaque:actor:a",
            "runtime_profile_ref": "opaque:runtime:codex",
            "outcome": "use_succeeded",
            "opaque_refs": ["opaque:program:run-1"],
            "idempotency_source": "server",
            "score": 10,
        }
        first = self.call(
            "skills_use_report_submit",
            report=report,
            client_idempotency_key="client-1",
        )
        self.assertTrue(first["ok"])
        self.assertFalse(first["replay"])
        second = self.call(
            "skills_use_report_submit",
            report=report,
            client_idempotency_key="client-1",
        )
        self.assertTrue(second["replay"])
        conflict = self.call(
            "skills_use_report_submit",
            report=dict(report, outcome="use_failed"),
            client_idempotency_key="client-1",
        )
        self.assertEqual(conflict["error"], "idempotency_conflict")
        status = self.call("skills_use_report_status_get", report_id="opaque:report:10")
        self.assertEqual(status["status"], "accepted")
        self.assertEqual(
            self.call("skills_use_report_submit", report=dict(report, prompt="secret transcript"))["error"],
            "validation_failed",
        )
        librarian = self.call("skills_librarian_status_get")
        self.assertIn("librarian", librarian)

    def test_degraded_store_is_sanitised(self) -> None:
        self.store.available = False
        result = self.call(
            "skills_feedback_submit",
            feedback={"skill_id": "research", "feedback_id": "opaque:fb:1", "kind": "friction"},
        )
        self.assertEqual(result["error"], "store_unavailable")
        self.assertTrue(result["store"]["fail_closed"])
        self.assertNotIn("postgres://", json_dump(result))


def json_dump(value) -> str:
    import json

    return json.dumps(value)


if __name__ == "__main__":
    unittest.main()
