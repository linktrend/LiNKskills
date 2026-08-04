#!/usr/bin/env python3
"""Graceful drain / signal / timeout / restart tests (no live services)."""

from __future__ import annotations

import signal
import sys
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path
from typing import Any, List

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATHS = [
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
]
for path in PACKAGE_PATHS:
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.ops import (  # noqa: E402
    DrainState,
    GatewayMetrics,
    persist_and_close_store,
    run_graceful_shutdown,
    shutdown_timeout_s,
    wait_for_in_flight,
)
from linkskills_gateway.server import (  # noqa: E402
    create_server,
    install_shutdown_signals,
    serve_until_shutdown,
)
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402


class _FakeStore:
    def __init__(self) -> None:
        self.flushed = False
        self.closed = False
        self.rows: List[str] = []

    def flush(self) -> None:
        self.flushed = True

    def close(self) -> None:
        self.closed = True

    def save(self, value: str) -> None:
        self.rows.append(value)


class ShutdownUnitTests(unittest.TestCase):
    def test_shutdown_timeout_from_environ(self) -> None:
        self.assertEqual(shutdown_timeout_s({}), 30.0)
        self.assertEqual(
            shutdown_timeout_s({"LINKSKILLS_SHUTDOWN_TIMEOUT_S": "12.5"}),
            12.5,
        )
        self.assertEqual(
            shutdown_timeout_s({"LINKSKILLS_SHUTDOWN_TIMEOUT_S": "nope"}),
            30.0,
        )

    def test_wait_for_in_flight_drains_clean(self) -> None:
        metrics = GatewayMetrics()
        metrics.begin_work()
        ticks = {"n": 0}

        def clock() -> float:
            ticks["n"] += 1
            return float(ticks["n"])

        def sleep_fn(_s: float) -> None:
            metrics.end_work()

        clean, remaining = wait_for_in_flight(
            metrics,
            timeout_s=5.0,
            poll_interval_s=0.01,
            sleep_fn=sleep_fn,
            clock=clock,
        )
        self.assertTrue(clean)
        self.assertEqual(remaining, 0)

    def test_wait_for_in_flight_timeout(self) -> None:
        metrics = GatewayMetrics()
        metrics.begin_work()
        metrics.begin_work()
        clean, remaining = wait_for_in_flight(
            metrics,
            timeout_s=0.0,
            poll_interval_s=0.01,
            sleep_fn=lambda _s: None,
            clock=time.monotonic,
        )
        self.assertFalse(clean)
        self.assertEqual(remaining, 2)

    def test_run_graceful_shutdown_persists_and_closes(self) -> None:
        drain = DrainState()
        metrics = GatewayMetrics()
        store = _FakeStore()
        store.save("retryable-intent")
        result = run_graceful_shutdown(
            drain=drain,
            metrics=metrics,
            store=store,
            reason="test",
            timeout_s=1.0,
            sleep_fn=lambda _s: None,
        )
        self.assertTrue(result.clean)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(drain.snapshot()[0])
        self.assertEqual(drain.snapshot()[1], "test")
        self.assertTrue(store.flushed)
        self.assertTrue(store.closed)
        self.assertEqual(store.rows, ["retryable-intent"])

    def test_run_graceful_shutdown_timeout_exit_code(self) -> None:
        drain = DrainState()
        metrics = GatewayMetrics()
        metrics.begin_work()
        store = _FakeStore()
        result = run_graceful_shutdown(
            drain=drain,
            metrics=metrics,
            store=store,
            reason="timeout-test",
            timeout_s=0.0,
            sleep_fn=lambda _s: None,
        )
        self.assertFalse(result.drained)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.in_flight_remaining, 1)
        self.assertTrue(store.closed)

    def test_persist_and_close_none_store(self) -> None:
        flushed, closed = persist_and_close_store(None)
        self.assertFalse(flushed)
        self.assertFalse(closed)


class SignalDrainHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics = GatewayMetrics()
        self.drain = DrainState()
        self.store = _FakeStore()
        self.env = {
            "LINKSKILLS_AUTH_MODE": "local-test",
            "LINKSKILLS_STORE_PROBE": "0",
            "LINKSKILLS_GATEWAY_DURABLE": "0",
        }
        self.service = SkillsGatewayService(repo_root=REPO_ROOT)
        # Attach fake store for shutdown close path without durable backends.
        self.service._store = self.store  # noqa: SLF001 — test seam
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=self.service,
            verifier=LocalUnsignedClaimsVerifier(),
            metrics=self.metrics,
            drain=self.drain,
            environ=self.env,
        )
        self.port = int(self.httpd.server_address[1])
        self.thread = threading.Thread(
            target=self.httpd.serve_forever,
            name="gw-shutdown-test",
            daemon=True,
        )
        self.thread.start()

    def tearDown(self) -> None:
        try:
            self.httpd.shutdown()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.httpd.server_close()
        except Exception:  # noqa: BLE001
            pass
        self.thread.join(timeout=2.0)

    def _get(self, path: str) -> Any:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2.0)
        try:
            conn.request("GET", path)
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            return resp.status, body
        finally:
            conn.close()

    def test_signal_handler_enables_drain_and_stops_server(self) -> None:
        uninstall = install_shutdown_signals(self.httpd, drain=self.drain)
        try:
            status, _ = self._get("/health")
            self.assertEqual(status, 200)
            # Invoke the installed handler without OS signal delivery.
            request_stop = getattr(self.httpd, "linkskills_request_stop")
            request_stop(signal.SIGTERM)
            self.thread.join(timeout=3.0)
            self.assertFalse(self.thread.is_alive())
            draining, reason = self.drain.snapshot()
            self.assertTrue(draining)
            self.assertIn(str(int(signal.SIGTERM)), reason)
        finally:
            uninstall()

    def test_serve_until_shutdown_closes_store(self) -> None:
        # Stop the setUp serve thread first; serve_until_shutdown owns its loop.
        self.httpd.shutdown()
        self.thread.join(timeout=2.0)

        metrics = GatewayMetrics()
        drain = DrainState()
        store = _FakeStore()
        store.save("pre-restart")
        service = SkillsGatewayService(repo_root=REPO_ROOT)
        service._store = store  # noqa: SLF001
        httpd = create_server(
            "127.0.0.1",
            0,
            service=service,
            verifier=LocalUnsignedClaimsVerifier(),
            metrics=metrics,
            drain=drain,
            environ=self.env,
        )

        def stop_soon() -> None:
            time.sleep(0.05)
            getattr(httpd, "linkskills_request_stop")(signal.SIGINT)

        stopper = threading.Thread(target=stop_soon, daemon=True)
        # install_signals=True so linkskills_request_stop exists.
        stopper.start()
        result = serve_until_shutdown(
            httpd,
            drain=drain,
            metrics=metrics,
            store=store,
            timeout_s=2.0,
            install_signals=True,
        )
        stopper.join(timeout=2.0)
        self.assertTrue(result.clean)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(store.flushed)
        self.assertTrue(store.closed)
        # Restart-safe: prior persisted rows remain on the store object.
        restarted = _FakeStore()
        restarted.rows = list(store.rows)
        self.assertEqual(restarted.rows, ["pre-restart"])


if __name__ == "__main__":
    unittest.main()
