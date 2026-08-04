#!/usr/bin/env python3
"""Wave-12: fail-closed idempotency key requirement for every WRITE_OPERATIONS member."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

os.environ.setdefault(
    "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
    "linkskills-local-eval-runner-issuer-key-not-for-production",
)
os.environ.setdefault("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "allow_unproven")

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "tool_runtime",
    REPO_ROOT / "packages" / "mcp_server",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.persistence import SqliteGatewayStore  # noqa: E402
from linkskills_gateway.server import create_server  # noqa: E402
from linkskills_gateway.service import (  # noqa: E402
    IDEMPOTENCY_KEY_MAX_CHARS,
    WRITE_OPERATIONS,
    ServiceError,
    SkillsGatewayService,
)
from linkskills_mcp.server import SkillsMcpServer  # noqa: E402


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


def _write_params(operation: str) -> Dict[str, Any]:
    """Minimal params so rejection cannot be attributed to missing business fields."""
    if operation == "skills_run_start":
        return {
            "skill_id": "usable-demo",
            "runtime_profile_tags": ["cursor-macos"],
        }
    if operation in {
        "skills_run_update",
        "skills_run_complete",
        "skills_run_fail",
        "skills_feedback_submit",
        "skills_trace_candidate_submit",
    }:
        base = {"run_id": "00000000-0000-4000-8000-000000000001"}
        if operation == "skills_run_update":
            base["progress"] = {"step": 1}
        if operation == "skills_run_complete":
            base["classification"] = "success"
        if operation == "skills_run_fail":
            base["error_class"] = "test"
            base["message"] = "fail"
        if operation == "skills_feedback_submit":
            base["skill_id"] = "usable-demo"
            base["kind"] = "correction"
            base["notes"] = "n"
        if operation == "skills_trace_candidate_submit":
            base["skill_id"] = "usable-demo"
            base["summary"] = "s"
        return base
    if operation == "skills_tool_invoke":
        return {
            "tool_id": "text-echo",
            "skill_id": "usable-demo",
            "dry_run": True,
            "argv": ["--help"],
        }
    raise AssertionError(f"unmapped write op {operation}")


INVALID_KEY_CASES: List[Tuple[str, Any, str]] = [
    ("missing", "__MISSING__", "idempotency_key_required"),
    ("null", None, "idempotency_key_required"),
    ("empty", "", "idempotency_key_required"),
    ("whitespace", "   \t  ", "idempotency_key_required"),
    ("leading_ws", " key", "idempotency_key_invalid"),
    ("malformed_slash", "bad/key", "idempotency_key_invalid"),
    ("malformed_space", "bad key", "idempotency_key_invalid"),
    ("malformed_type", 12345, "idempotency_key_invalid"),
    ("oversized", "k" * (IDEMPOTENCY_KEY_MAX_CHARS + 1), "idempotency_key_invalid"),
]


def _snapshot(service: SkillsGatewayService) -> Dict[str, Any]:
    store = service._store
    assert isinstance(store, SqliteGatewayStore)
    runs = store._conn.execute("select count(*) as c from skill_runs").fetchone()["c"]
    events = store._conn.execute("select count(*) as c from gateway_events").fetchone()[
        "c"
    ]
    idem = store._conn.execute("select count(*) as c from idempotency").fetchone()["c"]
    side = store._conn.execute(
        "select count(*) as c from side_effect_intents"
    ).fetchone()["c"]
    return {
        "runs_db": int(runs),
        "events_db": int(events),
        "idempotency_db": int(idem),
        "side_effects_db": int(side),
        "runs_cache": sorted(service._runs.keys()),
        "events_cache": len(service._events),
        "feedback_cache": len(service._feedback),
        "traces_cache": len(service._trace_candidates),
    }


class WriteIdempotencyKeyRequiredTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.service = SkillsGatewayService(
            repo_root=REPO_ROOT,
            catalog_index=_usable_catalog(),
            state_dir=Path(self.tmp.name),
        )
        self.actor = _actor()
        self.token = mint_test_bearer({"permittedOperations": ["*"]})
        self.mcp = SkillsMcpServer(
            service=self.service, verifier=LocalUnsignedClaimsVerifier()
        )
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=self.service,
            verifier=LocalUnsignedClaimsVerifier(),
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        store = self.service._store
        if isinstance(store, SqliteGatewayStore):
            store.close()
        self.tmp.cleanup()

    def test_write_operations_set_is_complete(self) -> None:
        self.assertEqual(
            set(WRITE_OPERATIONS),
            {
                "skills_run_start",
                "skills_run_update",
                "skills_run_complete",
                "skills_run_fail",
                "skills_tool_invoke",
                "skills_feedback_submit",
                "skills_trace_candidate_submit",
            },
        )

    def test_reads_still_work_without_idempotency_key(self) -> None:
        env = self.service.dispatch("skills_list", {}, actor=self.actor)
        self.assertIsNone(env.get("error"))
        self.assertGreaterEqual(env["data"]["count"], 1)

    def _assert_untouched(
        self, before: Dict[str, Any], *, invoke_mock: Optional[mock.MagicMock]
    ) -> None:
        after = _snapshot(self.service)
        self.assertEqual(before, after)
        if invoke_mock is not None:
            invoke_mock.assert_not_called()

    def test_service_dispatch_rejects_invalid_keys_for_every_write_op(self) -> None:
        for operation in sorted(WRITE_OPERATIONS):
            for case_name, raw_key, expected_code in INVALID_KEY_CASES:
                with self.subTest(surface="service", operation=operation, case=case_name):
                    before = _snapshot(self.service)
                    params = _write_params(operation)
                    kwargs: Dict[str, Any] = {"actor": self.actor}
                    if raw_key != "__MISSING__":
                        kwargs["idempotency_key"] = raw_key
                    with mock.patch(
                        "linkskills_tool_runtime.invoke.invoke_tool"
                    ) as invoke_mock:
                        with self.assertRaises(ServiceError) as ctx:
                            self.service.dispatch(operation, params, **kwargs)
                    self.assertEqual(ctx.exception.code, expected_code)
                    self.assertEqual(ctx.exception.http_status, 400)
                    self._assert_untouched(
                        before,
                        invoke_mock=invoke_mock
                        if operation == "skills_tool_invoke"
                        else None,
                    )

    def test_http_gateway_rejects_invalid_keys_for_every_write_op(self) -> None:
        for operation in sorted(WRITE_OPERATIONS):
            for case_name, raw_key, expected_code in INVALID_KEY_CASES:
                with self.subTest(surface="http", operation=operation, case=case_name):
                    before = _snapshot(self.service)
                    body: Dict[str, Any] = {"params": _write_params(operation)}
                    headers = {
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    }
                    if raw_key == "__MISSING__":
                        pass
                    elif case_name == "null":
                        body["idempotency_key"] = None
                    elif isinstance(raw_key, str) or raw_key is None:
                        body["idempotency_key"] = raw_key
                    else:
                        body["idempotency_key"] = raw_key
                    raw = json.dumps(body)
                    headers["Content-Length"] = str(len(raw))
                    with mock.patch(
                        "linkskills_tool_runtime.invoke.invoke_tool"
                    ) as invoke_mock:
                        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
                        conn.request(
                            "POST",
                            f"/v1/{operation}",
                            body=raw,
                            headers=headers,
                        )
                        resp = conn.getresponse()
                        payload = json.loads(resp.read().decode("utf-8"))
                        conn.close()
                    self.assertEqual(resp.status, 400, payload)
                    self.assertEqual((payload.get("error") or {}).get("code"), expected_code)
                    self._assert_untouched(
                        before,
                        invoke_mock=invoke_mock
                        if operation == "skills_tool_invoke"
                        else None,
                    )

    def test_mcp_rejects_invalid_keys_for_every_write_op(self) -> None:
        for operation in sorted(WRITE_OPERATIONS):
            for case_name, raw_key, expected_code in INVALID_KEY_CASES:
                with self.subTest(surface="mcp", operation=operation, case=case_name):
                    before = _snapshot(self.service)
                    args: Dict[str, Any] = {"params": _write_params(operation)}
                    if raw_key != "__MISSING__":
                        args["idempotency_key"] = raw_key
                    with mock.patch(
                        "linkskills_tool_runtime.invoke.invoke_tool"
                    ) as invoke_mock:
                        with self.assertRaises(ServiceError) as ctx:
                            self.mcp.call_tool(
                                operation,
                                args,
                                authorization=f"Bearer {self.token}",
                            )
                    self.assertEqual(ctx.exception.code, expected_code)
                    self._assert_untouched(
                        before,
                        invoke_mock=invoke_mock
                        if operation == "skills_tool_invoke"
                        else None,
                    )

    def test_valid_key_still_mutates_once(self) -> None:
        before = _snapshot(self.service)
        env = self.service.dispatch(
            "skills_run_start",
            _write_params("skills_run_start"),
            actor=self.actor,
            idempotency_key="valid-key-1",
        )
        self.assertIsNone(env.get("error"))
        after = _snapshot(self.service)
        self.assertEqual(after["runs_db"], before["runs_db"] + 1)
        self.assertEqual(after["events_db"], before["events_db"] + 1)
        self.assertEqual(len(after["runs_cache"]), len(before["runs_cache"]) + 1)


if __name__ == "__main__":
    unittest.main()
