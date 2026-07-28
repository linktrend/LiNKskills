#!/usr/bin/env python3
"""Wave-7 idempotency concurrency/lease and launch-target artifact tests."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
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
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.persistence import (  # noqa: E402
    InMemoryGatewayStore,
    SqliteGatewayStore,
    gateway_db_path,
)
from linkskills_gateway.service import ServiceError, SkillsGatewayService  # noqa: E402
from validator import (  # noqa: E402
    load_launch_target_skill_ids,
    validate_launch_target_canonical_artifacts,
)


class IdempotencyConcurrencyTests(unittest.TestCase):
    def test_concurrent_identical_requests_single_reserve(self) -> None:
        store = InMemoryGatewayStore()
        outcomes: list[str] = []
        barrier = threading.Barrier(8)

        def worker() -> None:
            barrier.wait()
            outcome, _ = store.reserve_idempotency("a", "skills_run_update", "k1", "hash-same")
            outcomes.append(outcome)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda _: worker(), range(8)))
        self.assertEqual(outcomes.count("reserved"), 1)
        self.assertEqual(outcomes.count("in_progress"), 7)
        self.assertNotIn("conflict", outcomes)

    def test_in_progress_blocks_second_execution_on_service(self) -> None:
        catalog = {
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
        service = SkillsGatewayService(repo_root=REPO_ROOT, catalog_index=catalog)
        actor = LocalUnsignedClaimsVerifier().verify(
            f"Bearer {mint_test_bearer({'permittedOperations': ['*']})}"
        )
        started = service.dispatch(
            "skills_run_start",
            {"skill_id": "usable-demo", "runtime_profile_tags": ["cursor-macos"]},
            actor=actor,
            idempotency_key="start-w7",
        )
        run_id = started.get("run_id") or (started.get("data") or {}).get("run_id")
        params = {"run_id": run_id, "progress": {"step": 1}}
        from linkskills_gateway.persistence import canonical_request_hash

        request_hash = canonical_request_hash(
            {
                "actor_id": actor.actor_id,
                "org_id": actor.org_id,
                "operation": "skills_run_update",
                "params": params,
            }
        )
        outcome, _ = service._store.reserve_idempotency(
            actor.actor_id, "skills_run_update", "upd-w7", request_hash
        )
        self.assertEqual(outcome, "reserved")
        with self.assertRaises(ServiceError) as ctx:
            service.dispatch(
                "skills_run_update",
                dict(params),
                actor=actor,
                idempotency_key="upd-w7",
            )
        self.assertEqual(ctx.exception.code, "idempotency_in_progress")

    def test_stale_lease_reclaim_same_hash(self) -> None:
        store = InMemoryGatewayStore()
        outcome, _ = store.reserve_idempotency("a", "op", "k", "h1")
        self.assertEqual(outcome, "reserved")
        key = store._idempotency_key("a", "op", "k")
        store._idempotency[key]["lease_expires_at"] = "2000-01-01T00:00:00Z"
        outcome2, _ = store.reserve_idempotency("a", "op", "k", "h1")
        self.assertEqual(outcome2, "reserved")

    def test_same_hash_replay_after_complete(self) -> None:
        store = InMemoryGatewayStore()
        store.reserve_idempotency("a", "op", "k", "h1")
        store.complete_idempotency("a", "op", "k", "h1", {"ok": True})
        outcome, cached = store.reserve_idempotency("a", "op", "k", "h1")
        self.assertEqual(outcome, "replay")
        self.assertEqual(cached, {"ok": True})

    def test_different_hash_conflict(self) -> None:
        store = InMemoryGatewayStore()
        store.reserve_idempotency("a", "op", "k", "h1")
        outcome, _ = store.reserve_idempotency("a", "op", "k", "h2")
        self.assertEqual(outcome, "conflict")

    def test_sqlite_concurrent_reserve_and_stale_lease(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SqliteGatewayStore(gateway_db_path(Path(tmp)))
            outcomes: list[str] = []
            barrier = threading.Barrier(6)

            def worker() -> None:
                barrier.wait()
                outcome, _ = store.reserve_idempotency("a", "op", "sqlite-k", "hash")
                outcomes.append(outcome)

            with ThreadPoolExecutor(max_workers=6) as pool:
                list(pool.map(lambda _: worker(), range(6)))
            self.assertEqual(outcomes.count("reserved"), 1)
            self.assertEqual(outcomes.count("in_progress"), 5)

            # Force stale lease via SQL, then reclaim.
            store._conn.execute(
                "update idempotency set lease_expires_at = '2000-01-01T00:00:00Z'"
            )
            store._conn.commit()
            outcome, _ = store.reserve_idempotency("a", "op", "sqlite-k", "hash")
            self.assertEqual(outcome, "reserved")
            store.complete_idempotency("a", "op", "sqlite-k", "hash", {"done": True})
            outcome2, cached = store.reserve_idempotency("a", "op", "sqlite-k", "hash")
            self.assertEqual(outcome2, "replay")
            self.assertEqual(cached, {"done": True})
            store.close()


class LaunchTargetCanonicalArtifactTests(unittest.TestCase):
    def test_canary_launch_targets_have_required_artifacts(self) -> None:
        ids = load_launch_target_skill_ids(REPO_ROOT)
        self.assertGreaterEqual(len(ids), 10)
        for skill_id in ids:
            skill_path = REPO_ROOT / "skills" / skill_id
            ok, errors = validate_launch_target_canonical_artifacts(
                skill_path, launch_target_ids=ids
            )
            self.assertTrue(ok, msg=f"{skill_id}: {errors}")
            for rel in (
                "references/skill-pack.json",
                "references/eval-suite.json",
                "references/execution-profile.json",
            ):
                self.assertTrue((skill_path / rel).is_file(), msg=f"missing {skill_id}/{rel}")

    def test_missing_launch_artifact_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "git-safeguard"
            skill.mkdir()
            (skill / "references").mkdir()
            ok, errors = validate_launch_target_canonical_artifacts(
                skill, launch_target_ids=["git-safeguard"]
            )
            self.assertFalse(ok)
            self.assertTrue(any("missing canonical Skill Pack" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
