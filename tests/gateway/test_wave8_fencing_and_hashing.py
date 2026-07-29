#!/usr/bin/env python3
"""Wave-8 mutation-safe idempotency fencing and shared canonical hashing."""

from __future__ import annotations

import json
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
    REPO_ROOT / "packages" / "publisher",
    REPO_ROOT / "packages" / "eval_runner",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_core.hashing import (  # noqa: E402
    build_skill_bundle_manifest,
    eval_suite_file_hash,
    execution_profile_identity_hash,
    skill_release_hash,
    stamp_execution_profile,
    verify_execution_profile_hashes,
)
from linkskills_eval_runner.executor import compute_skill_release_hash  # noqa: E402
from linkskills_gateway.persistence import (  # noqa: E402
    InMemoryGatewayStore,
    SqliteGatewayStore,
    gateway_db_path,
)
from linkskills_gateway.service import SkillRun  # noqa: E402
from linkskills_publisher.bundle import build_skill_bundle  # noqa: E402
from validator import (  # noqa: E402
    load_launch_target_skill_ids,
    validate_launch_target_canonical_artifacts,
)


def _sample_run(run_id: str, *, outcome: str = "ok") -> SkillRun:
    return SkillRun(
        run_id=run_id,
        skill_id="demo",
        version="1.0.0",
        release_hash="rel",
        profile_hash="prof",
        actor_id="actor-a",
        org_id="org-a",
        status="completed",
        created_at="2026-07-29T00:00:00Z",
        updated_at="2026-07-29T00:00:00Z",
        outcome={"result": outcome},
        idempotency_key="idem-1",
    )


class MutationSafeIdempotencyTests(unittest.TestCase):
    def test_crash_after_mutation_rolls_back_atomic_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SqliteGatewayStore(gateway_db_path(Path(tmp)))
            mutations = {"count": 0}

            def mutator():
                mutations["count"] += 1
                store.save_run(_sample_run("run-crash"))
                raise RuntimeError("simulated crash after mutation")

            with self.assertRaises(RuntimeError):
                store.run_atomic_idempotent("a", "skills_run_start", "k", "h1", mutator)
            self.assertIsNone(store.get_run("run-crash"))
            self.assertEqual(mutations["count"], 1)
            # Lease still reserved; reclaim after expiry and complete once.
            store._conn.execute(
                "update idempotency set lease_expires_at = '2000-01-01T00:00:00Z'"
            )
            store._conn.commit()

            def mutator_ok():
                mutations["count"] += 1
                store.save_run(_sample_run("run-ok", outcome="once"))
                return {"data": {"run_id": "run-ok"}}

            done = store.run_atomic_idempotent("a", "skills_run_start", "k", "h1", mutator_ok)
            self.assertEqual(done.outcome, "replay")
            loaded = store.get_run("run-ok")
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded["outcome"]["result"], "once")
            self.assertEqual(mutations["count"], 2)
            store.close()

    def test_stale_reclaim_rejects_late_original_completion(self) -> None:
        store = InMemoryGatewayStore()
        original = store.reserve_idempotency("a", "op", "k", "h1")
        self.assertEqual(original.outcome, "reserved")
        key = store._idempotency_key("a", "op", "k")
        store._idempotency[key]["lease_expires_at"] = "2000-01-01T00:00:00Z"
        reclaimed = store.reserve_idempotency("a", "op", "k", "h1")
        self.assertEqual(reclaimed.outcome, "reserved")
        self.assertNotEqual(original.fence_token, reclaimed.fence_token)
        with self.assertRaises(ValueError) as ctx:
            store.complete_idempotency(
                "a",
                "op",
                "k",
                "h1",
                {"late": True},
                fence_token=original.fence_token or "",
            )
        self.assertIn("fence rejected", str(ctx.exception))
        store.complete_idempotency(
            "a",
            "op",
            "k",
            "h1",
            {"winner": True},
            fence_token=reclaimed.fence_token or "",
        )
        replay = store.reserve_idempotency("a", "op", "k", "h1")
        self.assertEqual(replay.envelope, {"winner": True})

    def test_concurrent_same_key_single_domain_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SqliteGatewayStore(gateway_db_path(Path(tmp)))
            barrier = threading.Barrier(8)
            results: list[tuple[str, bool]] = []
            lock = threading.Lock()
            counter = {"n": 0}

            def worker(_: int) -> None:
                barrier.wait()

                def mutator():
                    counter["n"] += 1
                    run_id = f"run-{counter['n']}"
                    store.save_run(_sample_run(run_id, outcome=str(counter["n"])))
                    return {"data": {"run_id": run_id, "n": counter["n"]}}

                try:
                    result = store.run_atomic_idempotent(
                        "a", "skills_run_start", "same-key", "same-hash", mutator
                    )
                    with lock:
                        results.append((result.outcome, result.fence_token is not None))
                except Exception as exc:  # pragma: no cover - unexpected
                    with lock:
                        results.append((f"error:{exc}", False))

            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(worker, range(8)))
            # Fresh atomic completion returns replay+fence; prior completions return replay without fence.
            fresh = [r for r in results if r == ("replay", True)]
            cached = [r for r in results if r == ("replay", False)]
            in_progress = [r for r in results if r[0] == "in_progress"]
            self.assertEqual(len(fresh), 1, msg=results)
            self.assertEqual(len(fresh) + len(cached) + len(in_progress), 8, msg=results)
            self.assertEqual(counter["n"], 1)
            rows = store._conn.execute("select count(*) as c from skill_runs").fetchone()
            self.assertEqual(int(rows["c"]), 1)
            store.close()

    def test_same_hash_replay_and_different_hash_conflict(self) -> None:
        store = InMemoryGatewayStore()
        first = store.run_atomic_idempotent(
            "a",
            "op",
            "k",
            "hash-a",
            lambda: {"ok": 1},
        )
        self.assertEqual(first.outcome, "replay")
        replay = store.run_atomic_idempotent(
            "a",
            "op",
            "k",
            "hash-a",
            lambda: {"ok": 2},
        )
        self.assertEqual(replay.outcome, "replay")
        self.assertEqual(replay.envelope, {"ok": 1})
        conflict = store.run_atomic_idempotent(
            "a",
            "op",
            "k",
            "hash-b",
            lambda: {"ok": 3},
        )
        self.assertEqual(conflict.outcome, "conflict")

    def test_external_side_effect_intent_fence_and_downstream_key(self) -> None:
        store = InMemoryGatewayStore()
        reserved = store.reserve_idempotency("a", "skills_tool_invoke", "ext-1", "h-ext")
        assert reserved.fence_token is not None
        from linkskills_gateway.persistence import stable_downstream_idempotency_key

        downstream = stable_downstream_idempotency_key(
            actor_id="a",
            org_id="org",
            operation="skills_tool_invoke",
            idempotency_key="ext-1",
            request_hash="h-ext",
        )
        intent = store.record_side_effect_intent(
            "a",
            "skills_tool_invoke",
            "ext-1",
            fence_token=reserved.fence_token,
            downstream_key=downstream,
            request_hash="h-ext",
        )
        self.assertEqual(intent["status"], "intent")
        store.complete_side_effect_intent(
            "a",
            "skills_tool_invoke",
            "ext-1",
            fence_token=reserved.fence_token,
            result={"tool": "ok"},
        )
        saved = store.get_side_effect_intent("a", "skills_tool_invoke", "ext-1")
        assert saved is not None
        self.assertEqual(saved["status"], "result")
        self.assertEqual(saved["downstream_key"], downstream)
        # Stale fence cannot complete after reclaim.
        key = store._idempotency_key("a", "skills_tool_invoke", "ext-1")
        store._idempotency[key]["lease_expires_at"] = "2000-01-01T00:00:00Z"
        store._idempotency[key]["status"] = "reserved"
        store._idempotency[key]["envelope"] = None
        reclaimed = store.reserve_idempotency("a", "skills_tool_invoke", "ext-1", "h-ext")
        with self.assertRaises(ValueError):
            store.complete_idempotency(
                "a",
                "skills_tool_invoke",
                "ext-1",
                "h-ext",
                {"late": True},
                fence_token=reserved.fence_token,
            )
        with self.assertRaises(ValueError):
            store.complete_side_effect_intent(
                "a",
                "skills_tool_invoke",
                "ext-1",
                fence_token=reserved.fence_token,
                result={"late": True},
            )
        # Reclaim preserves durable result.
        preserved = store.record_side_effect_intent(
            "a",
            "skills_tool_invoke",
            "ext-1",
            fence_token=reclaimed.fence_token or "",
            downstream_key=downstream,
            request_hash="h-ext",
        )
        self.assertEqual(preserved["status"], "result")
        self.assertEqual(preserved["result"], {"tool": "ok"})
        self.assertIsNotNone(reclaimed.fence_token)


class CanonicalHashingTests(unittest.TestCase):
    def test_publisher_and_eval_runner_share_release_hash(self) -> None:
        skill = REPO_ROOT / "skills" / "git-safeguard"
        publisher = build_skill_bundle(skill)
        shared = build_skill_bundle_manifest(skill)
        self.assertEqual(publisher["bundle_hash"], shared["bundle_hash"])
        self.assertEqual(publisher["content_hash"], shared["content_hash"])
        self.assertEqual(
            compute_skill_release_hash(skill),
            skill_release_hash(skill),
        )

    def test_launch_target_profiles_hash_agree_clean_repeated_runs(self) -> None:
        ids = load_launch_target_skill_ids(REPO_ROOT)
        self.assertGreaterEqual(len(ids), 10)
        for skill_id in ids:
            skill = REPO_ROOT / "skills" / skill_id
            stamped_a = stamp_execution_profile(skill)
            stamped_b = stamp_execution_profile(skill)
            self.assertEqual(stamped_a, stamped_b, msg=skill_id)
            on_disk = json.loads(
                (skill / "references" / "execution-profile.json").read_text(encoding="utf-8")
            )
            self.assertEqual(on_disk["skill_bundle_hash"], stamped_a["skill_bundle_hash"])
            self.assertEqual(on_disk["eval_suite_hash"], stamped_a["eval_suite_hash"])
            self.assertEqual(on_disk["profile_hash"], stamped_a["profile_hash"])
            self.assertEqual(
                on_disk["profile_hash"],
                execution_profile_identity_hash(on_disk),
            )
            self.assertEqual(on_disk["eval_suite_hash"], eval_suite_file_hash(skill))
            errors = verify_execution_profile_hashes(skill, on_disk)
            self.assertEqual(errors, [], msg=f"{skill_id}: {errors}")
            ok, val_errors = validate_launch_target_canonical_artifacts(
                skill, launch_target_ids=ids
            )
            self.assertTrue(ok, msg=f"{skill_id}: {val_errors}")
            # Two clean skill_release_hash reads agree.
            self.assertEqual(skill_release_hash(skill), skill_release_hash(skill))


if __name__ == "__main__":
    unittest.main()
