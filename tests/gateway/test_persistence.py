#!/usr/bin/env python3
"""Gateway durable SQLite persistence tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "gateway"))

from linkskills_gateway.persistence import (  # noqa: E402
    InMemoryGatewayStore,
    SqliteGatewayStore,
    gateway_db_path,
    open_gateway_store,
)
from linkskills_gateway.service import SkillRun, SkillsGatewayService  # noqa: E402


class GatewayPersistenceTests(unittest.TestCase):
    def test_idempotency_collision_returns_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SqliteGatewayStore(gateway_db_path(Path(tmp)))
            first = {"operation": "skills_run_start", "data": {"run_id": "r1"}}
            store.put_idempotent("actor-1", "skills_run_start", "key-1", first)
            second = store.put_idempotent(
                "actor-1",
                "skills_run_start",
                "key-1",
                first,
            )
            self.assertEqual(second["data"]["run_id"], "r1")
            store.close()

    def test_idempotency_different_payload_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SqliteGatewayStore(gateway_db_path(Path(tmp)))
            store.put_idempotent(
                "actor-1",
                "skills_run_start",
                "key-1",
                {"operation": "skills_run_start", "data": {"run_id": "r1"}},
            )
            with self.assertRaises(ValueError):
                store.put_idempotent(
                    "actor-1",
                    "skills_run_start",
                    "key-1",
                    {"operation": "skills_run_start", "data": {"run_id": "r2"}},
                )
            store.close()

    def test_atomic_reserve_binds_request_hash(self) -> None:
        store = InMemoryGatewayStore()
        reserved = store.reserve_idempotency("a", "op", "k", "hash-1")
        self.assertEqual(reserved.outcome, "reserved")
        self.assertIsNone(reserved.envelope)
        self.assertIsNotNone(reserved.fence_token)
        # Second reserve while in-flight must not execute again.
        busy = store.reserve_idempotency("a", "op", "k", "hash-1")
        self.assertEqual(busy.outcome, "in_progress")
        store.complete_idempotency(
            "a", "op", "k", "hash-1", {"ok": True}, fence_token=reserved.fence_token or ""
        )
        replay = store.reserve_idempotency("a", "op", "k", "hash-1")
        self.assertEqual(replay.outcome, "replay")
        self.assertEqual(replay.envelope, {"ok": True})
        conflict = store.reserve_idempotency("a", "op", "k", "hash-2")
        self.assertEqual(conflict.outcome, "conflict")

    def test_run_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SqliteGatewayStore(gateway_db_path(Path(tmp)))
            run = SkillRun(
                run_id="run-1",
                skill_id="demo",
                version="1.0.0",
                release_hash="rel",
                profile_hash="prof",
                actor_id="actor-1",
                org_id="org-1",
                status="started",
                created_at="2026-07-28T00:00:00Z",
                updated_at="2026-07-28T00:00:00Z",
            )
            store.save_run(run)
            loaded = store.get_run("run-1")
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded["actor_id"], "actor-1")
            store.close()

    def test_service_uses_sqlite_when_state_dir_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            service = SkillsGatewayService(
                repo_root=REPO_ROOT,
                state_dir=state_dir,
                catalog_index={"skills": []},
            )
            self.assertTrue((state_dir / "gateway.sqlite").is_file())
            self.assertIsInstance(service._store, SqliteGatewayStore)

    def test_default_service_stays_in_memory(self) -> None:
        service = SkillsGatewayService(repo_root=REPO_ROOT, catalog_index={"skills": []})
        self.assertIsInstance(service._store, InMemoryGatewayStore)


if __name__ == "__main__":
    unittest.main()
