"""Stdlib HTTP JSON API for LiNKskills Gateway.

Routes:
  GET  /health
  GET  /ready
  GET  /metrics
  GET  /drain
  POST /drain
  POST /drain/cancel
  POST /v1/{operation}

Compatibility note: ``packages/client/linkskills_client/compat.py`` wraps
``lib.skill_runtime`` so existing Python consumers can migrate toward this
gateway without an immediate cutover.

Signals: ``SIGTERM`` / ``SIGINT`` stop intake (drain), wait boundedly for
in-flight work, persist/close the store, then exit with an honest code.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, Mapping, Optional, Tuple, Type
from urllib.parse import urlparse

from .auth import (
    AuthConfigurationError,
    AuthError,
    resolve_claims_verifier,
)
from .ops import (
    DrainState,
    GatewayMetrics,
    ShutdownResult,
    auth_config_present,
    drain_from_environ,
    run_graceful_shutdown,
    shutdown_timeout_s,
    store_probe_configured,
)
from .service import OPERATIONS, ServiceError, SkillsGatewayService


def _json_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def make_handler(
    service: SkillsGatewayService,
    verifier: Optional[Any] = None,
    *,
    metrics: Optional[GatewayMetrics] = None,
    drain: Optional[DrainState] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> Type[BaseHTTPRequestHandler]:
    # Never default to unsigned decoding. Missing production authenticator fails closed.
    auth = resolve_claims_verifier(verifier=verifier)
    stats = metrics if metrics is not None else GatewayMetrics()
    drain_state = drain if drain is not None else drain_from_environ(environ)
    env = environ if environ is not None else os.environ

    class LiNKskillsGateway(BaseHTTPRequestHandler):
        server_version = "LiNKskillsGateway/0.1"

        def log_message(self, fmt: str, *args: Any) -> None:
            # Quiet by default; tests and operators can wrap if needed.
            return

        def _send(self, status: int, payload: Dict[str, Any]) -> None:
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_text(self, status: int, body: str, *, content_type: str) -> None:
            raw = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _read_json(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
            length = int(self.headers.get("Content-Length") or "0")
            if length <= 0:
                return {}, None
            if length > 1_000_000:
                return None, "payload_too_large"
            raw = self.rfile.read(length)
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return None, "invalid_json"
            if data is None:
                return {}, None
            if not isinstance(data, dict):
                return None, "json_object_required"
            return data, None

        def _ready_payload(self) -> Dict[str, Any]:
            configured, auth_mode, detail = auth_config_present(env)
            draining, _reason = drain_state.snapshot()
            return service.ready(
                auth_configured=configured,
                auth_mode=auth_mode,
                auth_detail=detail,
                draining=draining,
                probe_store=store_probe_configured(env),
            )

        def do_GET(self) -> None:  # noqa: N802
            stats.inc_request()
            path = urlparse(self.path).path.rstrip("/") or "/"
            if path == "/health":
                # Liveness only — process up.
                self._send(200, service.health())
                return
            if path == "/ready":
                ready = self._ready_payload()
                stats.inc_ready(ready=bool(ready.get("ready")))
                self._send(200 if ready.get("ready") else 503, ready)
                return
            if path == "/metrics":
                ready = self._ready_payload()
                draining, _ = drain_state.snapshot()
                text = stats.render_prometheus(
                    ready_gauge=1 if ready.get("ready") else 0,
                    draining_gauge=1 if draining else 0,
                )
                self._send_text(
                    200,
                    text,
                    content_type="text/plain; version=0.0.4; charset=utf-8",
                )
                return
            if path == "/drain":
                draining, reason = drain_state.snapshot()
                self._send(
                    200,
                    {
                        "draining": draining,
                        "reason": reason,
                        "in_flight": stats.snapshot()["in_flight"],
                    },
                )
                return
            self._send(
                404,
                {
                    "error": {
                        "code": "not_found",
                        "message": f"Unknown path: {path}",
                        "retryable": False,
                    }
                },
            )

        def do_POST(self) -> None:  # noqa: N802
            stats.inc_request()
            path = urlparse(self.path).path.rstrip("/") or "/"

            if path == "/drain":
                body, err = self._read_json()
                if err:
                    self._send(
                        400,
                        {
                            "error": {
                                "code": err,
                                "message": err.replace("_", " "),
                                "retryable": False,
                            }
                        },
                    )
                    return
                reason = "endpoint"
                if isinstance(body, dict) and body.get("reason"):
                    # Bound, non-secret operator note only.
                    reason = str(body.get("reason"))[:120]
                drain_state.enable(reason=reason)
                self._send(
                    200,
                    {
                        "draining": True,
                        "reason": reason,
                        "in_flight": stats.snapshot()["in_flight"],
                    },
                )
                return

            if path == "/drain/cancel":
                # Discard body if present.
                self._read_json()
                drain_state.disable()
                self._send(
                    200,
                    {
                        "draining": False,
                        "reason": "",
                        "in_flight": stats.snapshot()["in_flight"],
                    },
                )
                return

            prefix = "/v1/"
            if not path.startswith(prefix):
                self._send(
                    404,
                    {
                        "error": {
                            "code": "not_found",
                            "message": f"Unknown path: {path}",
                            "retryable": False,
                        }
                    },
                )
                return

            draining, drain_reason = drain_state.snapshot()
            if draining:
                stats.inc_drain_reject()
                self._send(
                    503,
                    {
                        "error": {
                            "code": "draining",
                            "message": "Gateway is draining; rejecting new work",
                            "retryable": True,
                            "reason": drain_reason,
                        }
                    },
                )
                return

            operation = path[len(prefix) :]
            if operation not in OPERATIONS:
                self._send(
                    404,
                    {
                        "error": {
                            "code": "unknown_operation",
                            "message": f"Unknown operation: {operation}",
                            "retryable": False,
                        }
                    },
                )
                return

            body, err = self._read_json()
            if err:
                self._send(
                    400,
                    {
                        "error": {
                            "code": err,
                            "message": err.replace("_", " "),
                            "retryable": False,
                        }
                    },
                )
                return

            assert body is not None
            request_id = str(
                self.headers.get("X-Request-Id")
                or body.get("request_id")
                or uuid.uuid4()
            )
            # Header is authoritative when present; otherwise body field (any JSON type).
            # Do not coerce/truthiness-strip — service fail-closed validation owns the contract.
            if "Idempotency-Key" in self.headers:
                idempotency_key: Any = self.headers.get("Idempotency-Key")
            elif "idempotency_key" in body:
                idempotency_key = body.get("idempotency_key")
            else:
                idempotency_key = None
            params = body.get("params") if isinstance(body.get("params"), dict) else body

            # Strip envelope-only keys when body is used as params.
            if "params" not in body:
                params = {
                    k: v
                    for k, v in params.items()
                    if k
                    not in {
                        "request_id",
                        "idempotency_key",
                        "actor_id",
                        "actor_kind",
                        "org_id",
                        "scopes",
                        "exp",
                        "credential_id",
                        "platform_actor_id",
                        "actor",
                        "identity",
                        "claims",
                        "platform_claims",
                    }
                }

            authorization = self.headers.get("Authorization")
            idempotency_id = (
                idempotency_key if isinstance(idempotency_key, str) else None
            )
            stats.begin_work()
            try:
                # Pass original body + headers so spoofed identity is visible.
                # Never accept X-Actor-* override headers as authority.
                actor = auth.verify(
                    authorization,
                    request_payload=body,
                    request_headers=dict(self.headers.items()),
                    required_operation=operation,
                )
                envelope = service.dispatch(
                    operation,
                    params,
                    actor=actor,
                    request_id=request_id,
                    idempotency_key=idempotency_key,
                )
                self._send(200, envelope)
            except AuthError as exc:
                stats.inc_auth_fail()
                status = 401
                if exc.code in {
                    "auth_forbidden",
                    "auth_spoof_rejected",
                    "auth_revoked",
                    "auth_unsigned_rejected",
                }:
                    status = 403
                self._send(
                    status,
                    service.envelope(
                        actor=None,
                        operation=operation,
                        request_id=request_id,
                        idempotency_id=idempotency_id,
                        error={
                            "code": exc.code,
                            "message": exc.message,
                            "retryable": False,
                        },
                    ),
                )
            except ServiceError as exc:
                self._send(
                    exc.http_status,
                    service.envelope(
                        actor=None,
                        operation=operation,
                        request_id=request_id,
                        idempotency_id=idempotency_id,
                        error={
                            "code": exc.code,
                            "message": exc.message,
                            "retryable": exc.retryable,
                        },
                    ),
                )
            except Exception as exc:
                # Never drop the connection on unexpected store/runtime faults.
                # Log type only — no tokens, DSNs, or traceback bodies to clients.
                err_type = type(exc).__name__
                sys.stderr.write(
                    f"linkskills_gateway internal_error op={operation} "
                    f"request_id={request_id} type={err_type}\n"
                )
                self._send(
                    500,
                    service.envelope(
                        actor=None,
                        operation=operation,
                        request_id=request_id,
                        idempotency_id=idempotency_id,
                        error={
                            "code": "internal_error",
                            "message": "Internal server error",
                            "retryable": True,
                        },
                    ),
                )
            finally:
                stats.end_work()

    return LiNKskillsGateway


def create_server(
    host: str = "127.0.0.1",
    port: int = 8787,
    *,
    service: Optional[SkillsGatewayService] = None,
    verifier: Optional[Any] = None,
    metrics: Optional[GatewayMetrics] = None,
    drain: Optional[DrainState] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> ThreadingHTTPServer:
    svc = service or SkillsGatewayService()
    handler = make_handler(
        svc,
        verifier=verifier,
        metrics=metrics,
        drain=drain,
        environ=environ,
    )
    httpd = ThreadingHTTPServer((host, port), handler)
    # Attach runtime handles for signal/drain shutdown (tests may override).
    httpd.linkskills_service = svc  # type: ignore[attr-defined]
    httpd.linkskills_metrics = metrics  # type: ignore[attr-defined]
    httpd.linkskills_drain = drain  # type: ignore[attr-defined]
    return httpd


def _store_from_service(service: Any) -> Any:
    """Best-effort store handle for shutdown close (private attr by design)."""
    return getattr(service, "_store", None)


def install_shutdown_signals(
    httpd: ThreadingHTTPServer,
    *,
    drain: DrainState,
    reason_prefix: str = "signal",
) -> Callable[[], None]:
    """Install SIGTERM/SIGINT handlers that enable drain and stop the HTTP loop.

    ``httpd.shutdown()`` must not run on the serve thread; we dispatch it on a
    daemon helper thread. Returns an uninstall callable for tests.
    """
    once = threading.Event()

    def _request_stop(signum: int, _frame: Any = None) -> None:
        if once.is_set():
            return
        once.set()
        drain.enable(reason=f"{reason_prefix}:{signum}")
        # Wake serve_forever from another thread (stdlib contract).
        stopper = threading.Thread(
            target=httpd.shutdown,
            name="linkskills-gateway-shutdown",
            daemon=True,
        )
        stopper.start()

    previous_term = signal.signal(signal.SIGTERM, _request_stop)
    previous_int = signal.signal(signal.SIGINT, _request_stop)

    def uninstall() -> None:
        signal.signal(signal.SIGTERM, previous_term)
        signal.signal(signal.SIGINT, previous_int)

    # Expose for unit tests that invoke the handler without OS signals.
    httpd.linkskills_request_stop = _request_stop  # type: ignore[attr-defined]
    return uninstall


def serve_until_shutdown(
    httpd: ThreadingHTTPServer,
    *,
    drain: DrainState,
    metrics: GatewayMetrics,
    store: Any = None,
    timeout_s: Optional[float] = None,
    install_signals: bool = True,
) -> ShutdownResult:
    """Serve forever until SIGTERM/SIGINT/KeyboardInterrupt, then graceful exit."""
    uninstall: Optional[Callable[[], None]] = None
    if install_signals:
        uninstall = install_shutdown_signals(httpd, drain=drain)
    try:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            drain.enable(reason="signal:KeyboardInterrupt")
    finally:
        if uninstall is not None:
            uninstall()
        result = run_graceful_shutdown(
            drain=drain,
            metrics=metrics,
            store=store,
            reason=drain.snapshot()[1] or "shutdown",
            timeout_s=timeout_s,
        )
        try:
            httpd.server_close()
        except Exception:  # noqa: BLE001 — exit path must remain honest
            pass
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="LiNKskills Gateway HTTP server")
    parser.add_argument("--host", default=os.environ.get("LINKSKILLS_GATEWAY_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("LINKSKILLS_GATEWAY_PORT", "8787")),
    )
    args = parser.parse_args()
    try:
        verifier = resolve_claims_verifier()
    except AuthConfigurationError as exc:
        print(f"linkskills-gateway auth fail-closed: {exc.message}", file=sys.stderr)
        raise SystemExit(2) from exc
    metrics = GatewayMetrics()
    drain = drain_from_environ()
    service = SkillsGatewayService()
    httpd = create_server(
        args.host,
        args.port,
        service=service,
        verifier=verifier,
        metrics=metrics,
        drain=drain,
    )
    timeout = shutdown_timeout_s()
    print(f"linkskills-gateway listening on http://{args.host}:{args.port}")
    result = serve_until_shutdown(
        httpd,
        drain=drain,
        metrics=metrics,
        store=_store_from_service(service),
        timeout_s=timeout,
    )
    if result.timed_out:
        print(
            "linkskills-gateway shutdown timed out with "
            f"in_flight={result.in_flight_remaining}",
            file=sys.stderr,
        )
    else:
        print(
            "linkskills-gateway shutdown clean "
            f"(store_closed={result.store_closed})",
            file=sys.stderr,
        )
    raise SystemExit(result.exit_code)


if __name__ == "__main__":
    main()
