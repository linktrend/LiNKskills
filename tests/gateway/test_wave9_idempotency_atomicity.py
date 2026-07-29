#!/usr/bin/env python3
"""Wave-9 adversarial idempotency: service cache atomicity, fencing, downstream keys."""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

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
from linkskills_gateway.persistence import (  # noqa: E402
    SqliteGatewayStore,
    gateway_db_path,
    stable_downstream_idempotency_key,
)
from linkskills_gateway.service import ServiceError, SkillsGatewayService  # noqa: E402


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


class ServiceStateAtomicityTests(unittest.TestCase):
    def test_crash_after_mutation_restores_service_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            service = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=state_dir,
            )
            actor = _actor()
            store = service._store
            assert isinstance(store, SqliteGatewayStore)
            store._crash_after_mutation = True

            with self.assertRaises(RuntimeError):
                service.dispatch(
                    "skills_run_start",
                    {
                        "skill_id": "usable-demo",
                        "runtime_profile_tags": ["cursor-macos"],
                    },
                    actor=actor,
                    idempotency_key="crash-start-1",
                )

            # Service-visible cache must not retain a rolled-back run.
            self.assertEqual(service._runs, {})
            rows = store._conn.execute("select count(*) as c from skill_runs").fetchone()
            self.assertEqual(int(rows["c"]), 0)
            events = store._conn.execute(
                "select count(*) as c from gateway_events"
            ).fetchone()
            self.assertEqual(int(events["c"]), 0)

            # Retry after crash — exactly one logical mutation (atomic txn left nothing).
            env = service.dispatch(
                "skills_run_start",
                {
                    "skill_id": "usable-demo",
                    "runtime_profile_tags": ["cursor-macos"],
                },
                actor=actor,
                idempotency_key="crash-start-1",
            )
            run_id = env.get("run_id") or (env.get("data") or {}).get("run_id")
            self.assertIsNotNone(run_id)
            self.assertIn(run_id, service._runs)
            self.assertIsNotNone(store.get_run(str(run_id)))
            rows = store._conn.execute("select count(*) as c from skill_runs").fetchone()
            self.assertEqual(int(rows["c"]), 1)
            # Replay does not create a second run.
            replay = service.dispatch(
                "skills_run_start",
                {
                    "skill_id": "usable-demo",
                    "runtime_profile_tags": ["cursor-macos"],
                },
                actor=actor,
                idempotency_key="crash-start-1",
            )
            replay_id = replay.get("run_id") or (replay.get("data") or {}).get("run_id")
            self.assertEqual(replay_id, run_id)
            rows = store._conn.execute("select count(*) as c from skill_runs").fetchone()
            self.assertEqual(int(rows["c"]), 1)
            store.close()

    def test_update_crash_does_not_diverge_cache_from_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=Path(tmp),
            )
            actor = _actor()
            started = service.dispatch(
                "skills_run_start",
                {"skill_id": "usable-demo", "runtime_profile_tags": ["cursor-macos"]},
                actor=actor,
                idempotency_key="upd-base",
            )
            run_id = started.get("run_id") or (started.get("data") or {}).get("run_id")
            before = service._runs[str(run_id)].status
            store = service._store
            assert isinstance(store, SqliteGatewayStore)
            store._crash_after_mutation = True
            with self.assertRaises(RuntimeError):
                service.dispatch(
                    "skills_run_update",
                    {"run_id": run_id, "progress": {"step": 1}},
                    actor=actor,
                    idempotency_key="upd-crash",
                )
            # Cache still shows pre-crash status; DB agrees.
            self.assertEqual(service._runs[str(run_id)].status, before)
            loaded = store.get_run(str(run_id))
            assert loaded is not None
            self.assertEqual(loaded["status"], before)
            store.close()


class ExternalResultFencingTests(unittest.TestCase):
    def test_old_worker_cannot_overwrite_result_after_reclaim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SqliteGatewayStore(gateway_db_path(Path(tmp)))
            first = store.reserve_idempotency("a", "skills_tool_invoke", "k", "h1")
            assert first.fence_token is not None
            downstream = stable_downstream_idempotency_key(
                actor_id="a",
                org_id="",
                operation="skills_tool_invoke",
                idempotency_key="k",
                request_hash="h1",
            )
            store.record_side_effect_intent(
                "a",
                "skills_tool_invoke",
                "k",
                fence_token=first.fence_token,
                downstream_key=downstream,
                request_hash="h1",
            )
            store.complete_side_effect_intent(
                "a",
                "skills_tool_invoke",
                "k",
                fence_token=first.fence_token,
                result={"v": 1},
            )
            # Simulate crash before idempotency complete, then reclaim.
            store._conn.execute(
                "update idempotency set lease_expires_at = '2000-01-01T00:00:00Z', "
                "status = 'reserved', envelope_json = null"
            )
            store._conn.commit()
            second = store.reserve_idempotency("a", "skills_tool_invoke", "k", "h1")
            assert second.fence_token is not None
            self.assertNotEqual(first.fence_token, second.fence_token)
            with self.assertRaises(ValueError):
                store.complete_side_effect_intent(
                    "a",
                    "skills_tool_invoke",
                    "k",
                    fence_token=first.fence_token,
                    result={"v": 999},
                )
            preserved = store.get_side_effect_intent("a", "skills_tool_invoke", "k")
            assert preserved is not None
            self.assertEqual(preserved["result"], {"v": 1})
            reconciled = store.record_side_effect_intent(
                "a",
                "skills_tool_invoke",
                "k",
                fence_token=second.fence_token,
                downstream_key=downstream,
                request_hash="h1",
            )
            self.assertEqual(reconciled["result"], {"v": 1})
            store.close()


class DownstreamKeyStabilityTests(unittest.TestCase):
    def test_downstream_key_stable_across_reclaim_and_propagated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=Path(tmp),
            )
            actor = _actor()
            # Find any packaged tool for dry-run invoke.
            tools_root = REPO_ROOT / "tools"
            tool_ids = [p.name for p in tools_root.iterdir() if p.is_dir()]
            self.assertTrue(tool_ids)
            tool_id = tool_ids[0]
            params = {
                "tool_id": tool_id,
                "skill_id": "usable-demo",
                "dry_run": True,
                "argv": ["--help"],
            }
            first = service.dispatch(
                "skills_tool_invoke",
                params,
                actor=actor,
                idempotency_key="tool-stable-1",
            )
            key1 = (first.get("data") or {}).get("downstream_idempotency_key")
            self.assertTrue(str(key1).startswith("lskills-downstream:"))
            self.assertIn("external_side_effect_at_least_once", first.get("warnings") or [])

            # Force reclaim path with durable result present.
            store = service._store
            assert isinstance(store, SqliteGatewayStore)
            store._conn.execute(
                "update idempotency set lease_expires_at = '2000-01-01T00:00:00Z', "
                "status = 'reserved', envelope_json = null"
            )
            store._conn.commit()
            second = service.dispatch(
                "skills_tool_invoke",
                params,
                actor=actor,
                idempotency_key="tool-stable-1",
            )
            self.assertIn("side_effect_reconciled", second.get("warnings") or [])
            key2 = (second.get("data") or {}).get("downstream_idempotency_key")
            # Reconciled payload is the prior data dict which includes the key.
            self.assertEqual(key1, key2)
            # Stable derivation from identity fields (not fence).
            from linkskills_gateway.persistence import canonical_request_hash

            request_hash = canonical_request_hash(
                {
                    "actor_id": actor.actor_id,
                    "org_id": actor.org_id,
                    "operation": "skills_tool_invoke",
                    "params": params,
                }
            )
            expected = stable_downstream_idempotency_key(
                actor_id=actor.actor_id,
                org_id=actor.org_id,
                operation="skills_tool_invoke",
                idempotency_key="tool-stable-1",
                request_hash=request_hash,
            )
            self.assertEqual(key1, expected)
            store.close()

    def test_invoke_tool_receives_downstream_key(self) -> None:
        from linkskills_tool_runtime.invoke import invoke_tool

        tools = [p for p in (REPO_ROOT / "tools").iterdir() if p.is_dir()]
        self.assertTrue(tools)
        tool_dir = tools[0]
        captured: dict = {}

        class FakeAdapter:
            kind = "local_process"

            def invoke(self, resolved, argv=None, *, cwd=None, env=None, **kwargs):
                captured["env"] = dict(env or {})
                from linkskills_tool_runtime.adapters import AdapterResult

                return AdapterResult(
                    ok=True,
                    exit_code=0,
                    stdout="ok",
                    stderr="",
                    metadata={},
                )

        with mock.patch(
            "linkskills_tool_runtime.invoke.LocalProcessAdapter",
            FakeAdapter,
        ):
            # Need version/hash for resolve — use dry path via resolve only when pins match.
            # Call invoke_tool with no pin may fail resolve; use resolve_tool first.
            from linkskills_tool_runtime.resolve import resolve_tool

            resolved = resolve_tool(tool_dir)
            result = invoke_tool(
                tool_dir,
                tool_id=resolved.tool_id,
                version=resolved.version,
                source_hash=resolved.descriptor.source_hash,
                adapter="local",
                downstream_idempotency_key="lskills-downstream:abc",
            )
        self.assertTrue(result.ok)
        self.assertEqual(
            captured["env"].get("LINKSKILLS_DOWNSTREAM_IDEMPOTENCY_KEY"),
            "lskills-downstream:abc",
        )
        self.assertEqual(
            result.metadata.get("downstream_idempotency_key"),
            "lskills-downstream:abc",
        )
        self.assertFalse(result.metadata.get("downstream_idempotency_exactly_once"))


class ConcurrentIdempotencyTests(unittest.TestCase):
    def test_concurrent_run_start_single_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=Path(tmp),
            )
            actor = _actor()
            barrier = threading.Barrier(6)
            outcomes: list[str] = []
            lock = threading.Lock()

            def worker(_: int) -> None:
                barrier.wait()
                try:
                    env = service.dispatch(
                        "skills_run_start",
                        {
                            "skill_id": "usable-demo",
                            "runtime_profile_tags": ["cursor-macos"],
                        },
                        actor=actor,
                        idempotency_key="concurrent-start",
                    )
                    with lock:
                        if "idempotent_replay" in (env.get("warnings") or []):
                            outcomes.append("replay")
                        else:
                            outcomes.append("fresh")
                except ServiceError as exc:
                    with lock:
                        outcomes.append(exc.code)

            with ThreadPoolExecutor(max_workers=6) as pool:
                list(pool.map(worker, range(6)))
            self.assertEqual(outcomes.count("fresh"), 1, msg=outcomes)
            self.assertEqual(
                outcomes.count("fresh")
                + outcomes.count("replay")
                + outcomes.count("idempotency_in_progress"),
                6,
                msg=outcomes,
            )
            store = service._store
            assert isinstance(store, SqliteGatewayStore)
            rows = store._conn.execute("select count(*) as c from skill_runs").fetchone()
            self.assertEqual(int(rows["c"]), 1)
            self.assertEqual(len(service._runs), 1)
            store.close()


if __name__ == "__main__":
    unittest.main()
