#!/usr/bin/env python3
"""Wave-10: request-local mutation batches + honest downstream acknowledgment.

Wave-11 replaced ContextVar ownership with explicit MutationContext + per-service
serialization; this file keeps the isolation and ack proofs under that model.
"""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402


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


class RequestLocalMutationBatchTests(unittest.TestCase):
    def test_two_thread_commit_and_crash_isolated_batches(self) -> None:
        """Different-key concurrent commit/crash under per-service serialization."""
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

            def worker(idem_key: str) -> None:
                try:
                    env = service.dispatch(
                        "skills_run_start",
                        {
                            "skill_id": "usable-demo",
                            "runtime_profile_tags": ["cursor-macos"],
                        },
                        actor=actor,
                        idempotency_key=idem_key,
                    )
                    run_id = env.get("run_id") or (env.get("data") or {}).get("run_id")
                    with lock:
                        outcomes[idem_key] = f"ok:{run_id}"
                except RuntimeError as exc:
                    with lock:
                        outcomes[idem_key] = f"crash:{exc}"

            with ThreadPoolExecutor(max_workers=2) as pool:
                futs = [
                    pool.submit(worker, "key-ok"),
                    pool.submit(worker, "key-crash"),
                ]
                for fut in futs:
                    fut.result(timeout=30)

            self.assertTrue(outcomes["key-ok"].startswith("ok:"), msg=outcomes)
            self.assertTrue(outcomes["key-crash"].startswith("crash:"), msg=outcomes)
            ok_run_id = outcomes["key-ok"].split(":", 1)[1]

            self.assertFalse(hasattr(service, "_mutation_batch"))

            # Committed request visible in DB and service cache.
            self.assertIn(ok_run_id, service._runs)
            self.assertIsNotNone(store.get_run(ok_run_id))

            # Crashed request left no durable or service-visible run.
            rows = store._conn.execute("select run_id from skill_runs").fetchall()
            run_ids = {str(r["run_id"]) for r in rows}
            self.assertEqual(run_ids, {ok_run_id})
            self.assertEqual(set(service._runs.keys()), {ok_run_id})

            events = store._conn.execute(
                "select count(*) as c from gateway_events"
            ).fetchone()
            self.assertEqual(int(events["c"]), 1)

            # Retry crashed key → exactly one additional logical mutation.
            retry = service.dispatch(
                "skills_run_start",
                {
                    "skill_id": "usable-demo",
                    "runtime_profile_tags": ["cursor-macos"],
                },
                actor=actor,
                idempotency_key="key-crash",
            )
            crash_run_id = retry.get("run_id") or (retry.get("data") or {}).get("run_id")
            self.assertIsNotNone(crash_run_id)
            self.assertNotEqual(crash_run_id, ok_run_id)
            rows = store._conn.execute("select count(*) as c from skill_runs").fetchone()
            self.assertEqual(int(rows["c"]), 2)
            self.assertEqual(len(service._runs), 2)
            self.assertEqual(set(service._runs.keys()), {ok_run_id, str(crash_run_id)})
            for rid in (ok_run_id, str(crash_run_id)):
                loaded = store.get_run(rid)
                assert loaded is not None
                self.assertEqual(service._runs[rid].status, loaded["status"])
            store.close()


class HonestDownstreamAckTests(unittest.TestCase):
    def test_propagated_not_honored_without_adapter_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = SkillsGatewayService(
                repo_root=REPO_ROOT,
                catalog_index=_usable_catalog(),
                state_dir=Path(tmp),
            )
            actor = _actor()
            tool_id = next(p.name for p in (REPO_ROOT / "tools").iterdir() if p.is_dir())
            env = service.dispatch(
                "skills_tool_invoke",
                {
                    "tool_id": tool_id,
                    "skill_id": "usable-demo",
                    "dry_run": True,
                    "argv": ["--help"],
                },
                actor=actor,
                idempotency_key="ack-dry-1",
            )
            data = env.get("data") or {}
            self.assertTrue(data.get("downstream_idempotency_propagated"))
            self.assertNotIn("downstream_idempotency_honored", data.get("output") or {})
            # Dry-run does not prove exactly-once.
            self.assertIn("external_side_effect_at_least_once", env.get("warnings") or [])
            # Must not claim honored merely because key appears in LiNKskills metadata.
            self.assertIsNot(data.get("downstream_idempotency_honored"), True)


if __name__ == "__main__":
    unittest.main()
