#!/usr/bin/env python3
"""Wave-11: DB commit/cache publish ordering + explicit MutationContext ownership."""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

os.environ.setdefault(
    "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
    "linkskills-local-eval-runner-issuer-key-not-for-production",
)
os.environ.setdefault("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "allow_unproven")
os.environ["LINKSKILLS_IDEMPOTENCY_LEASE_SECONDS"] = "2"

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "tool_runtime",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.persistence import SqliteGatewayStore  # noqa: E402
from linkskills_gateway.service import (  # noqa: E402
    MutationContext,
    SkillsGatewayService,
)


def _usable_catalog() -> dict:
    return {
        "skills": [
            {
                "skill_id": "usable-demo",
                "version": "1.0.0",
                "description": "usable demo",
                "format_profile": "heavy",
                "eval_suite_ref": "",
                "certification_state": "usable",
                "release_hash": "release-usable-1",
                "profile_hash": "profile-usable-1",
                "compatible_runtime_profiles": ["cursor-macos"],
            }
        ]
    }


def _actor():
    return LocalUnsignedClaimsVerifier().verify(
        f"Bearer {mint_test_bearer({'permittedOperations': ['*']})}"
    )


def _start_params() -> dict:
    return {
        "skill_id": "usable-demo",
        "runtime_profile_tags": ["cursor-macos"],
    }


class CommitBeforePublishSerializationTests(unittest.TestCase):
    def test_peer_blocked_until_cache_published(self) -> None:
        """A commits then pauses before publish; B cannot enter until A publishes."""
        with tempfile.TemporaryDirectory() as tmp:
            service = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=Path(tmp),
            )
            actor = _actor()
            store = service._store
            assert isinstance(store, SqliteGatewayStore)

            a_committed = threading.Event()
            release_a_publish = threading.Event()
            observed: dict[str, Any] = {"b_nonblocking_acquire": None}

            def pause_a(mutation: MutationContext) -> None:
                if observed.get("a_mutation") is not None:
                    # Peer requests must not re-enter this pause path for assertion.
                    return
                observed["a_mutation"] = mutation
                run_id = next(iter(mutation.runs))
                observed["a_run_id"] = run_id
                self.assertIsNotNone(store.get_run(run_id))
                self.assertNotIn(run_id, service._runs)
                a_committed.set()
                release_a_publish.wait(timeout=10)
                self.assertNotIn(run_id, service._runs)

            service._after_commit_before_publish_wait = pause_a

            outcomes: dict[str, str] = {}

            def worker_a() -> None:
                env = service.dispatch(
                    "skills_run_start",
                    _start_params(),
                    actor=actor,
                    idempotency_key="key-a",
                )
                rid = env.get("run_id") or (env.get("data") or {}).get("run_id")
                outcomes["a"] = str(rid)
                service._after_commit_before_publish_wait = None

            def worker_b() -> None:
                self.assertTrue(a_committed.wait(timeout=10))
                # While A holds the serialization boundary, B must not acquire it.
                observed["b_nonblocking_acquire"] = service._mutation_gate.acquire(
                    blocking=False
                )
                release_a_publish.set()
                # Wait until A finished publish + cleared the pause hook.
                deadline = time.time() + 10
                while time.time() < deadline and "a" not in outcomes:
                    time.sleep(0.01)
                env = service.dispatch(
                    "skills_run_start",
                    _start_params(),
                    actor=actor,
                    idempotency_key="key-b",
                )
                rid = env.get("run_id") or (env.get("data") or {}).get("run_id")
                outcomes["b"] = str(rid)

            with ThreadPoolExecutor(max_workers=2) as pool:
                fa = pool.submit(worker_a)
                fb = pool.submit(worker_b)
                fa.result(timeout=30)
                fb.result(timeout=30)

            self.assertIs(observed["b_nonblocking_acquire"], False)
            self.assertNotEqual(outcomes["a"], outcomes["b"])
            self.assertEqual(observed["a_run_id"], outcomes["a"])
            self.assertIn(outcomes["a"], service._runs)
            self.assertEqual(set(service._runs.keys()), {outcomes["a"], outcomes["b"]})
            for rid in (outcomes["a"], outcomes["b"]):
                loaded = store.get_run(rid)
                assert loaded is not None
                self.assertEqual(service._runs[rid].status, loaded["status"])
            events = store._conn.execute(
                "select count(*) as c from gateway_events"
            ).fetchone()
            self.assertEqual(int(events["c"]), 2)
            m = observed["a_mutation"]
            self.assertFalse(m.active)
            self.assertTrue(m.published)
            with self.assertRaises(RuntimeError):
                m.assert_writable(service)
            store.close()

    def test_update_reads_store_not_stale_cache_inside_boundary(self) -> None:
        """Inside an active mutation, _get_run loads store state, not stale cache."""
        with tempfile.TemporaryDirectory() as tmp:
            service = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=Path(tmp),
            )
            actor = _actor()
            store = service._store
            assert isinstance(store, SqliteGatewayStore)

            start = service.dispatch(
                "skills_run_start",
                _start_params(),
                actor=actor,
                idempotency_key="seed-start",
            )
            run_id = str(start.get("run_id") or (start.get("data") or {}).get("run_id"))
            # Poison the service cache with a stale status while DB stays started.
            service._runs[run_id].status = "completed"
            service._runs[run_id].outcome = {"classification": "poison"}

            env = service.dispatch(
                "skills_run_update",
                {"run_id": run_id, "progress": {"step": 1}},
                actor=actor,
                idempotency_key="update-against-store",
            )
            self.assertEqual(env["data"]["status"], "in_progress")
            loaded = store.get_run(run_id)
            assert loaded is not None
            self.assertEqual(loaded["status"], "in_progress")
            self.assertEqual(service._runs[run_id].status, "in_progress")
            store.close()


class NestedServiceMutationTests(unittest.TestCase):
    def test_nested_service_does_not_join_parent_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            service1 = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=Path(tmp1),
            )
            service2 = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=Path(tmp2),
            )
            actor = _actor()
            nested: dict[str, Any] = {}

            original = service1.op_skills_run_start

            def wrapped(
                *,
                actor,
                params,
                idempotency_key,
                mutation: Optional[MutationContext] = None,
            ):
                nested["parent"] = mutation
                assert mutation is not None
                mutation.assert_writable(service1)
                # Nested call on another service must use its own context.
                env2 = service2.dispatch(
                    "skills_run_start",
                    _start_params(),
                    actor=actor,
                    idempotency_key="nested-s2",
                )
                nested["s2_run"] = env2.get("run_id") or (env2.get("data") or {}).get(
                    "run_id"
                )
                # Parent context remains writable and must not contain s2 runs.
                mutation.assert_writable(service1)
                self.assertNotIn(str(nested["s2_run"]), mutation.runs)
                # Foreign service identity must fail closed.
                with self.assertRaises(RuntimeError):
                    mutation.assert_writable(service2)
                return original(
                    actor=actor,
                    params=params,
                    idempotency_key=idempotency_key,
                    mutation=mutation,
                )

            service1.op_skills_run_start = wrapped  # type: ignore[method-assign]

            env1 = service1.dispatch(
                "skills_run_start",
                _start_params(),
                actor=actor,
                idempotency_key="nested-s1",
            )
            s1_run = str(env1.get("run_id") or (env1.get("data") or {}).get("run_id"))
            s2_run = str(nested["s2_run"])
            self.assertNotEqual(s1_run, s2_run)
            self.assertIn(s1_run, service1._runs)
            self.assertNotIn(s2_run, service1._runs)
            self.assertIn(s2_run, service2._runs)
            self.assertNotIn(s1_run, service2._runs)
            self.assertIsNotNone(service1._store.get_run(s1_run))
            self.assertIsNotNone(service2._store.get_run(s2_run))
            parent = nested["parent"]
            self.assertFalse(parent.active)
            self.assertTrue(parent.published)
            service1._store.close()
            service2._store.close()


class ExpiredMutationContextTests(unittest.TestCase):
    def test_async_child_fails_closed_after_parent_publishes(self) -> None:
        """Capture context before publish; use after parent finishes → fail closed."""
        with tempfile.TemporaryDirectory() as tmp:
            service = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=Path(tmp),
            )
            actor = _actor()
            captured: dict[str, MutationContext] = {}

            def capture(mutation: MutationContext) -> None:
                captured["ctx"] = mutation
                # Still writable at pause (commit done, publish pending).
                mutation.assert_writable(service)

            service._after_commit_before_publish_wait = capture

            env = service.dispatch(
                "skills_run_start",
                _start_params(),
                actor=actor,
                idempotency_key="async-child",
            )
            run_id = str(env.get("run_id") or (env.get("data") or {}).get("run_id"))
            ctx = captured["ctx"]
            self.assertTrue(ctx.published)
            self.assertFalse(ctx.active)
            self.assertEqual(ctx.service_id, id(service))
            self.assertEqual(ctx.request_id, env["request_id"])
            self.assertGreaterEqual(ctx.generation, 1)

            with self.assertRaises(RuntimeError):
                ctx.assert_writable(service)
            with self.assertRaises(RuntimeError):
                service._persist_run(service._runs[run_id], mutation=ctx)
            with self.assertRaises(RuntimeError):
                service._record_local_event({"type": "late"}, mutation=ctx)

            # Pre-request equality: only the one logical event from the parent.
            store = service._store
            assert isinstance(store, SqliteGatewayStore)
            events = store._conn.execute(
                "select count(*) as c from gateway_events"
            ).fetchone()
            self.assertEqual(int(events["c"]), 1)
            loaded = store.get_run(run_id)
            assert loaded is not None
            self.assertEqual(service._runs[run_id].status, loaded["status"])
            store.close()


class ConcurrentCrashRetryTests(unittest.TestCase):
    def test_different_key_commit_crash_retry_no_lost_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=Path(tmp),
            )
            actor = _actor()
            store = service._store
            assert isinstance(store, SqliteGatewayStore)
            store._crash_after_mutation_keys = {"key-crash"}

            outcomes: dict[str, str] = {}
            lock = threading.Lock()

            def worker(key: str) -> None:
                try:
                    env = service.dispatch(
                        "skills_run_start",
                        _start_params(),
                        actor=actor,
                        idempotency_key=key,
                    )
                    rid = env.get("run_id") or (env.get("data") or {}).get("run_id")
                    with lock:
                        outcomes[key] = f"ok:{rid}"
                except RuntimeError as exc:
                    with lock:
                        outcomes[key] = f"crash:{exc}"

            with ThreadPoolExecutor(max_workers=2) as pool:
                futs = [pool.submit(worker, "key-ok"), pool.submit(worker, "key-crash")]
                for fut in futs:
                    fut.result(timeout=30)

            self.assertTrue(outcomes["key-ok"].startswith("ok:"), msg=outcomes)
            self.assertTrue(outcomes["key-crash"].startswith("crash:"), msg=outcomes)
            ok_id = outcomes["key-ok"].split(":", 1)[1]

            # Crash rolled back DB and never published cache.
            rows = {str(r["run_id"]) for r in store._conn.execute("select run_id from skill_runs")}
            self.assertEqual(rows, {ok_id})
            self.assertEqual(set(service._runs.keys()), {ok_id})

            retry = service.dispatch(
                "skills_run_start",
                _start_params(),
                actor=actor,
                idempotency_key="key-crash",
            )
            crash_id = str(retry.get("run_id") or (retry.get("data") or {}).get("run_id"))
            self.assertNotEqual(crash_id, ok_id)
            self.assertEqual(
                {str(r["run_id"]) for r in store._conn.execute("select run_id from skill_runs")},
                {ok_id, crash_id},
            )
            self.assertEqual(set(service._runs.keys()), {ok_id, crash_id})
            events = store._conn.execute(
                "select count(*) as c from gateway_events"
            ).fetchone()
            self.assertEqual(int(events["c"]), 2)
            for rid in (ok_id, crash_id):
                loaded = store.get_run(rid)
                assert loaded is not None
                self.assertEqual(service._runs[rid].status, loaded["status"])
            store.close()


if __name__ == "__main__":
    unittest.main()
