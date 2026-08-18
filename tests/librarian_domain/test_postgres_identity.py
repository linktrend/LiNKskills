#!/usr/bin/env python3
"""Unit tests for PostgresReviewQueueStore bound-identity enforcement (no DB)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "librarian_domain"))


def _make_store(*, service_scope: str = "actor"):
    from linkskills_librarian.postgres_store import PostgresReviewQueueStore

    with mock.patch("linkskills_librarian.postgres_store.psycopg") as psycopg_mod:
        conn = mock.MagicMock()
        conn.info.transaction_status = 0
        psycopg_mod.connect.return_value = conn
        psycopg_mod.pq.TransactionStatus.IDLE = 0
        # Skip require_table probe.
        with mock.patch.object(
            PostgresReviewQueueStore, "table_exists", return_value=True
        ):
            store = PostgresReviewQueueStore(
                "postgresql://" + "example/db",
                rls=True,
                require_table=True,
                service_scope=service_scope,
            )
    return store


class PostgresReviewQueueIdentityUnitTests(unittest.TestCase):
    def test_current_identity_is_bound_only(self) -> None:
        store = _make_store()
        try:
            self.assertEqual(store._current_identity(), ("", ""))
            store.bind_identity("actor-a", "org-a")
            self.assertEqual(store._current_identity(), ("actor-a", "org-a"))
        finally:
            store.close()

    def test_enqueue_rejects_absent_bound_identity(self) -> None:
        store = _make_store()
        try:
            with self.assertRaises(ValueError) as ctx:
                store.enqueue(
                    {
                        "review_id": "r1",
                        "kind": "general",
                        "actor_id": "actor-a",
                        "org_id": "org-a",
                    }
                )
            msg = str(ctx.exception)
            self.assertIn("bound identity", msg)
            self.assertIn("untrusted item fields", msg)
        finally:
            store.close()

    def test_enqueue_rejects_actor_disagreement(self) -> None:
        store = _make_store()
        try:
            store.bind_identity("actor-a", "org-a")
            with self.assertRaises(ValueError) as ctx:
                store.enqueue(
                    {
                        "review_id": "r1",
                        "kind": "general",
                        "actor_id": "actor-b",
                        "org_id": "org-a",
                    }
                )
            msg = str(ctx.exception)
            self.assertIn("actor_id", msg)
            self.assertIn("actor-b", msg)
            self.assertIn("actor-a", msg)
            self.assertIn("disagrees", msg)
            self.assertIn("bound identity", msg)
        finally:
            store.close()

    def test_enqueue_rejects_org_disagreement(self) -> None:
        store = _make_store()
        try:
            store.bind_identity("actor-a", "org-a")
            with self.assertRaises(ValueError) as ctx:
                store.enqueue(
                    {
                        "review_id": "r1",
                        "kind": "general",
                        "actor_id": "actor-a",
                        "org_id": "org-b",
                    }
                )
            msg = str(ctx.exception)
            self.assertIn("org_id", msg)
            self.assertIn("org-b", msg)
            self.assertIn("org-a", msg)
            self.assertIn("disagrees", msg)
        finally:
            store.close()

    def test_privileged_org_scope_still_rejects_forged_item_identity(self) -> None:
        store = _make_store(service_scope="org")
        try:
            store.bind_identity("svc-librarian", "org-a")
            with self.assertRaises(ValueError) as ctx:
                store.enqueue(
                    {
                        "review_id": "r1",
                        "kind": "general",
                        "actor_id": "forged-actor",
                        "org_id": "org-evil",
                    }
                )
            self.assertIn("disagrees", str(ctx.exception))
        finally:
            store.close()

    def test_assert_item_identity_allows_omit_or_match(self) -> None:
        store = _make_store()
        try:
            store._assert_item_identity_agrees(
                {}, bound_actor="actor-a", bound_org="org-a"
            )
            store._assert_item_identity_agrees(
                {"actor_id": "actor-a", "org_id": "org-a"},
                bound_actor="actor-a",
                bound_org="org-a",
            )
            store._assert_item_identity_agrees(
                {"actor_id": "", "org_id": ""},
                bound_actor="actor-a",
                bound_org="org-a",
            )
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
