#!/usr/bin/env python3
"""Unit tests: Gateway Postgres store GUCs from bound identity only (no DB)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "gateway"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))


def _make_store():
    from linkskills_gateway.postgres_store import PostgresGatewayStore

    with mock.patch("linkskills_gateway.postgres_store.psycopg") as psycopg_mod:
        conn = mock.MagicMock()
        conn.info.transaction_status = 0
        psycopg_mod.connect.return_value = conn
        psycopg_mod.pq.TransactionStatus.IDLE = 0
        store = PostgresGatewayStore("postgresql://example/db", rls=True)
    return store


class PostgresGatewayBoundIdentityUnitTests(unittest.TestCase):
    def test_current_identity_is_bound_only_ignores_kwargs(self) -> None:
        store = _make_store()
        try:
            self.assertEqual(store._current_identity(), ("", ""))
            store.bind_identity("actor-a", "org-a")
            self.assertEqual(store._current_identity(), ("actor-a", "org-a"))
            # Bound-only API: no override kwargs (TypeError if still accepted).
            with self.assertRaises(TypeError):
                store._current_identity(actor_id="actor-b")  # type: ignore[call-arg]
        finally:
            store.close()

    def test_require_bound_identity_fail_closed(self) -> None:
        store = _make_store()
        try:
            with self.assertRaises(ValueError) as ctx:
                store._require_bound_identity()
            self.assertIn("bound", str(ctx.exception).lower())
        finally:
            store.close()

    def test_reserve_rejects_forged_actor_before_sql(self) -> None:
        store = _make_store()
        try:
            store.bind_identity("actor-a", "org-a")
            with self.assertRaises(ValueError) as ctx:
                store.reserve_idempotency("actor-b", "op", "k1", "hash-1")
            msg = str(ctx.exception)
            self.assertIn("disagrees", msg)
            self.assertIn("bound identity", msg)
            store._conn.cursor.assert_not_called()
        finally:
            store.close()

    def test_append_feedback_rejects_forged_payload_before_sql(self) -> None:
        store = _make_store()
        try:
            store.bind_identity("actor-a", "org-a")
            with self.assertRaises(ValueError) as ctx:
                store.append_feedback(
                    {
                        "feedback_id": "11111111-1111-1111-1111-111111111111",
                        "actor_id": "actor-b",
                        "org_id": "org-b",
                        "kind": "other",
                    }
                )
            self.assertIn("disagrees", str(ctx.exception))
            store._conn.cursor.assert_not_called()
        finally:
            store.close()

    def test_append_trace_rejects_forged_org_before_sql(self) -> None:
        store = _make_store()
        try:
            store.bind_identity("actor-a", "org-a")
            with self.assertRaises(ValueError) as ctx:
                store.append_trace(
                    {
                        "candidate_id": "22222222-2222-2222-2222-222222222222",
                        "fingerprint": "fp-forge",
                        "actor_id": "actor-a",
                        "org_id": "org-c",
                    }
                )
            self.assertIn("org_id", str(ctx.exception))
            self.assertIn("disagrees", str(ctx.exception))
            store._conn.cursor.assert_not_called()
        finally:
            store.close()

    def test_append_event_rejects_missing_identity_before_sql(self) -> None:
        """Anonymous probe must fail closed — no SQL without bound identity."""
        store = _make_store()
        try:
            with self.assertRaises(ValueError) as ctx:
                store.append_event({"type": "anonymous-probe"})
            msg = str(ctx.exception)
            self.assertIn("postgres RLS requires", msg)
            self.assertIn("bound", msg.lower())
            store._conn.cursor.assert_not_called()
        finally:
            store.close()

    def test_append_event_rejects_partial_identity_before_sql(self) -> None:
        """Actor-only or org-only binding must fail closed before SQL."""
        store = _make_store()
        try:
            store.bind_identity("actor-a", "")
            with self.assertRaises(ValueError) as ctx:
                store.append_event({"type": "partial-actor"})
            self.assertIn("postgres RLS requires", str(ctx.exception))
            self.assertIn("org_id", str(ctx.exception))
            store._conn.cursor.assert_not_called()

            store.clear_identity()
            store._conn.cursor.reset_mock()
            store.bind_identity("", "org-a")
            with self.assertRaises(ValueError) as ctx:
                store.append_event({"type": "partial-org"})
            self.assertIn("postgres RLS requires", str(ctx.exception))
            self.assertIn("actor_id", str(ctx.exception))
            store._conn.cursor.assert_not_called()
        finally:
            store.close()

    def test_append_event_rejects_forged_payload_before_sql(self) -> None:
        store = _make_store()
        try:
            store.bind_identity("actor-a", "org-a")
            with self.assertRaises(ValueError) as ctx:
                store.append_event(
                    {"type": "evt", "actor_id": "actor-d", "org_id": "org-d"}
                )
            self.assertIn("disagrees", str(ctx.exception))
            store._conn.cursor.assert_not_called()
        finally:
            store.close()

    def test_append_event_payload_identity_cannot_satisfy_missing_bind(self) -> None:
        """Payload actor/org must not substitute for missing PACI bind."""
        store = _make_store()
        try:
            with self.assertRaises(ValueError) as ctx:
                store.append_event(
                    {
                        "type": "payload-only",
                        "actor_id": "actor-payload",
                        "org_id": "org-payload",
                    }
                )
            self.assertIn("postgres RLS requires", str(ctx.exception))
            store._conn.cursor.assert_not_called()
        finally:
            store.close()

    def test_save_run_rejects_unbound_payload_fallback(self) -> None:
        from linkskills_gateway.service import SkillRun

        store = _make_store()
        try:
            with self.assertRaises(ValueError) as ctx:
                store.save_run(
                    SkillRun(
                        run_id="33333333-3333-3333-3333-333333333333",
                        skill_id="demo",
                        version="1.0.0",
                        release_hash="rel",
                        profile_hash="prof",
                        actor_id="actor-payload",
                        org_id="org-payload",
                        status="started",
                        created_at="2026-08-03T00:00:00Z",
                        updated_at="2026-08-03T00:00:00Z",
                    )
                )
            self.assertIn("bound", str(ctx.exception).lower())
            store._conn.cursor.assert_not_called()
        finally:
            store.close()

    def test_assert_payload_allows_omit_or_match(self) -> None:
        store = _make_store()
        try:
            store._assert_payload_identity_agrees(
                {}, bound_actor="actor-a", bound_org="org-a"
            )
            store._assert_payload_identity_agrees(
                {"actor_id": "actor-a", "org_id": "org-a"},
                bound_actor="actor-a",
                bound_org="org-a",
            )
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
