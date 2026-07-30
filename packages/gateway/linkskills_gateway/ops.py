"""Gateway process ops: metrics, drain, auth-config probe, graceful shutdown.

Kept separate from auth/persistence core so packaging/ops lanes can evolve
without colliding with PACI or store adapter work.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Tuple

from .auth import AUTH_MODE_LOCAL_TEST, resolve_auth_mode

# Operator-facing timeout for SIGTERM/SIGINT drain wait (seconds).
ENV_SHUTDOWN_TIMEOUT_S = "LINKSKILLS_SHUTDOWN_TIMEOUT_S"
DEFAULT_SHUTDOWN_TIMEOUT_S = 30.0


def _truthy(raw: Optional[str]) -> bool:
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class DrainState:
    """Process-local graceful drain flag.

    When draining, reject new ``/v1/*`` work with 503 while allowing
    ``/health``, ``/ready``, ``/metrics``, and ``/drain`` probes.
    In-flight requests finish normally.
    """

    enabled: bool = False
    reason: str = ""
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def enable(self, reason: str = "operator") -> None:
        with self._lock:
            self.enabled = True
            self.reason = reason or "operator"

    def disable(self) -> None:
        with self._lock:
            self.enabled = False
            self.reason = ""

    def snapshot(self) -> Tuple[bool, str]:
        with self._lock:
            return self.enabled, self.reason


@dataclass(frozen=True)
class ShutdownResult:
    """Honest outcome of a bounded graceful shutdown attempt."""

    reason: str
    drained: bool
    timed_out: bool
    in_flight_remaining: int
    store_flushed: bool
    store_closed: bool
    exit_code: int

    @property
    def clean(self) -> bool:
        return self.drained and not self.timed_out and self.exit_code == 0


@dataclass
class GatewayMetrics:
    """In-process counters for Prometheus text exposition (no labels with secrets)."""

    requests_total: int = 0
    auth_fail_total: int = 0
    ready_total: int = 0
    not_ready_total: int = 0
    drain_rejects_total: int = 0
    in_flight: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def inc_request(self) -> None:
        with self._lock:
            self.requests_total += 1

    def begin_work(self) -> None:
        with self._lock:
            self.in_flight += 1

    def end_work(self) -> None:
        with self._lock:
            if self.in_flight > 0:
                self.in_flight -= 1

    def inc_auth_fail(self) -> None:
        with self._lock:
            self.auth_fail_total += 1

    def inc_ready(self, *, ready: bool) -> None:
        with self._lock:
            if ready:
                self.ready_total += 1
            else:
                self.not_ready_total += 1

    def inc_drain_reject(self) -> None:
        with self._lock:
            self.drain_rejects_total += 1

    def snapshot(self) -> Mapping[str, int]:
        with self._lock:
            return {
                "requests_total": self.requests_total,
                "auth_fail_total": self.auth_fail_total,
                "ready_total": self.ready_total,
                "not_ready_total": self.not_ready_total,
                "drain_rejects_total": self.drain_rejects_total,
                "in_flight": self.in_flight,
            }

    def render_prometheus(self, *, ready_gauge: int, draining_gauge: int) -> str:
        snap = self.snapshot()
        lines = [
            "# HELP linkskills_gateway_requests_total Total HTTP requests handled.",
            "# TYPE linkskills_gateway_requests_total counter",
            f"linkskills_gateway_requests_total {snap['requests_total']}",
            "# HELP linkskills_gateway_auth_fail_total Auth failures (401/403).",
            "# TYPE linkskills_gateway_auth_fail_total counter",
            f"linkskills_gateway_auth_fail_total {snap['auth_fail_total']}",
            "# HELP linkskills_gateway_ready_total Ready probe successes.",
            "# TYPE linkskills_gateway_ready_total counter",
            f"linkskills_gateway_ready_total {snap['ready_total']}",
            "# HELP linkskills_gateway_not_ready_total Ready probe failures.",
            "# TYPE linkskills_gateway_not_ready_total counter",
            f"linkskills_gateway_not_ready_total {snap['not_ready_total']}",
            "# HELP linkskills_gateway_drain_rejects_total Requests rejected while draining.",
            "# TYPE linkskills_gateway_drain_rejects_total counter",
            f"linkskills_gateway_drain_rejects_total {snap['drain_rejects_total']}",
            "# HELP linkskills_gateway_in_flight In-flight /v1 work units.",
            "# TYPE linkskills_gateway_in_flight gauge",
            f"linkskills_gateway_in_flight {snap['in_flight']}",
            "# HELP linkskills_gateway_ready 1 if last ready criteria would pass.",
            "# TYPE linkskills_gateway_ready gauge",
            f"linkskills_gateway_ready {int(ready_gauge)}",
            "# HELP linkskills_gateway_draining 1 if graceful drain is active.",
            "# TYPE linkskills_gateway_draining gauge",
            f"linkskills_gateway_draining {int(draining_gauge)}",
            "",
        ]
        return "\n".join(lines)


def drain_from_environ(environ: Optional[Mapping[str, str]] = None) -> DrainState:
    """Create DrainState; enable when LINKSKILLS_DRAIN is truthy."""
    env = environ if environ is not None else os.environ
    state = DrainState()
    if _truthy(env.get("LINKSKILLS_DRAIN")):
        state.enable(reason="env:LINKSKILLS_DRAIN")
    return state


def auth_config_present(
    environ: Optional[Mapping[str, str]] = None,
) -> Tuple[bool, str, str]:
    """Check auth *mode configuration* without loading secrets or authenticators.

    Returns ``(configured, auth_mode, detail)``.
    Production requires ``LINKSKILLS_PLATFORM_AUTHENTICATOR`` env string present
    in ``module:attr`` form — the module is **not** imported here.
    """
    env = environ if environ is not None else os.environ
    try:
        mode = resolve_auth_mode(env)
    except Exception as exc:  # noqa: BLE001 — surface as not configured
        return False, "unknown", f"auth_mode_invalid:{exc}"

    if mode == AUTH_MODE_LOCAL_TEST:
        return True, mode, "local-test"

    ref = str(env.get("LINKSKILLS_PLATFORM_AUTHENTICATOR") or "").strip()
    if not ref:
        return False, mode, "missing_authenticator_env"
    if ":" not in ref:
        return False, mode, "authenticator_env_malformed"
    # Presence-only check — do not import module or resolve secrets.
    return True, mode, "authenticator_env_present"


def store_probe_configured(environ: Optional[Mapping[str, str]] = None) -> bool:
    """True when operators asked for a store reachability probe.

    Production/stage postgres deployments always probe so /ready fails closed
    when the DSN or migration surface is unreachable. Local memory/sqlite
    stores only probe when explicitly requested.
    """
    env = environ if environ is not None else os.environ
    if _truthy(env.get("LINKSKILLS_STORE_PROBE")):
        return True
    if _truthy(env.get("LINKSKILLS_GATEWAY_DURABLE")):
        return True
    # Fail-closed readiness for production-like / explicit postgres store.
    try:
        from .persistence import is_production_like_env, resolve_gateway_store_mode

        if is_production_like_env(env):
            return True
        if resolve_gateway_store_mode(env) == "postgres":
            return True
    except Exception:  # noqa: BLE001 — misconfig still probes when DSN present
        pass
    # Explicit store URL / DSN name present (value may be a SecretRef name).
    for key in (
        "LINKSKILLS_STORE_URL",
        "LINKSKILLS_DATABASE_URL",
        "LINKSKILLS_POSTGRES_URL",
        "LINKSKILLS_GATEWAY_STORE",
    ):
        if key == "LINKSKILLS_GATEWAY_STORE":
            if str(env.get(key) or "").strip().lower() == "postgres":
                return True
            continue
        if str(env.get(key) or "").strip():
            return True
    return False


def shutdown_timeout_s(environ: Optional[Mapping[str, str]] = None) -> float:
    """Bounded drain wait from ``LINKSKILLS_SHUTDOWN_TIMEOUT_S`` (default 30s)."""
    env = environ if environ is not None else os.environ
    raw = str(env.get(ENV_SHUTDOWN_TIMEOUT_S) or "").strip()
    if not raw:
        return DEFAULT_SHUTDOWN_TIMEOUT_S
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_SHUTDOWN_TIMEOUT_S
    if value < 0:
        return DEFAULT_SHUTDOWN_TIMEOUT_S
    return value


def wait_for_in_flight(
    metrics: GatewayMetrics,
    *,
    timeout_s: float,
    poll_interval_s: float = 0.05,
    sleep_fn: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> Tuple[bool, int]:
    """Block until ``in_flight == 0`` or ``timeout_s`` elapses.

    Returns ``(drained_clean, remaining_in_flight)``.
    """
    deadline = clock() + max(0.0, float(timeout_s))
    while True:
        remaining = int(metrics.snapshot()["in_flight"])
        if remaining <= 0:
            return True, 0
        if clock() >= deadline:
            return False, remaining
        sleep_fn(max(0.0, min(poll_interval_s, deadline - clock())))


def persist_and_close_store(store: Any) -> Tuple[bool, bool]:
    """Best-effort flush then close a gateway store (no-op when unsupported).

    Durable writes are already committed per request; this closes DB handles
    honestly so supervisors can restart without leaked connections.
    Returns ``(flushed, closed)``.
    """
    flushed = False
    closed = False
    if store is None:
        return flushed, closed
    for attr in ("flush", "checkpoint", "commit"):
        hook = getattr(store, attr, None)
        if callable(hook):
            try:
                hook()
                flushed = True
                break
            except Exception:  # noqa: BLE001 — shutdown must continue to close
                break
    closer = getattr(store, "close", None)
    if callable(closer):
        closer()
        closed = True
    else:
        # In-memory / protocol objects without close are treated as already closed.
        closed = True
    return flushed, closed


def run_graceful_shutdown(
    *,
    drain: DrainState,
    metrics: GatewayMetrics,
    store: Any = None,
    reason: str = "signal",
    timeout_s: Optional[float] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> ShutdownResult:
    """Stop intake, drain in-flight work boundedly, persist/close store, exit code.

    Exit codes:
      - ``0`` — drain completed (in-flight reached 0) and store closed
      - ``1`` — drain timed out with work still in flight (honest incomplete exit)
    """
    drain.enable(reason=reason)
    bound = DEFAULT_SHUTDOWN_TIMEOUT_S if timeout_s is None else float(timeout_s)
    drained, remaining = wait_for_in_flight(
        metrics,
        timeout_s=bound,
        sleep_fn=sleep_fn,
        clock=clock,
    )
    flushed, closed = persist_and_close_store(store)
    exit_code = 0 if drained else 1
    return ShutdownResult(
        reason=reason,
        drained=drained,
        timed_out=not drained,
        in_flight_remaining=remaining,
        store_flushed=flushed,
        store_closed=closed,
        exit_code=exit_code,
    )
