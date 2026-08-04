"""Project-scoped Cursor stdio MCP proxy with PACI machine-token auth.

Cursor launches this module (not the bare MCP server) for ``LINKSKILLS_CANARY``.
The proxy:

1. Acquires short-lived PACI access tokens via ``PaciTokenClient`` /
   ``SkillsGatewayClient.from_env`` (SecretRef private key file only).
2. Forwards JSON-RPC to an in-process ``SkillsMcpServer`` **or** the HTTP
   Gateway, injecting ``Authorization`` server-side.
3. Never places bearer tokens in tool arguments, argv, logs, Git, or global
   Cursor config.

Modes (``LINKSKILLS_MCP_UPSTREAM``):

- ``http`` (production / canary default): PACI bearer injected as HTTP
  ``Authorization`` via durable stage Gateway (``GATEWAY_URL`` https).
- ``in-process``: PACI bearer injected into in-process MCP tool calls.
  Production/canary in-process is refuse-by-default; requires
  ``LINKSKILLS_MCP_ALLOW_INPROCESS_PRODUCTION=1`` plus
  ``LINKSKILLS_ENV=stage|production``, postgres store, and DSN.
  Local-test may use in-process without those gates.

Static bearers are refused for canary / production; local-test static path is
explicit ``LINKSKILLS_AUTH_MODE=local-test`` only (not canary).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from typing import Any, Dict, Mapping, Optional, TextIO

from linkskills_client.client import SkillsGatewayClient
from linkskills_client.paci_token_client import (
    AUTH_MODE_LOCAL_TEST,
    PaciAuthError,
    PaciConfigError,
    PaciTokenClient,
    PaciTokenError,
    PaciTransientError,
    paci_env_configured,
    resolve_auth_mode,
)
from linkskills_gateway.auth import AuthError
from linkskills_gateway.persistence import (
    resolve_database_dsn,
    resolve_gateway_store_mode,
    is_production_like_env,
)
from linkskills_gateway.service import OPERATIONS

from .server import (
    PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    SkillsMcpServer,
    _tool_schema,
)

logger = logging.getLogger(__name__)

ENV_UPSTREAM = "LINKSKILLS_MCP_UPSTREAM"
ENV_ALLOW_INPROCESS_PRODUCTION = "LINKSKILLS_MCP_ALLOW_INPROCESS_PRODUCTION"
UPSTREAM_IN_PROCESS = "in-process"
UPSTREAM_HTTP = "http"
CANARY_ENV = "LINKSKILLS_CANARY"

# Auth-related keys stripped from tool arguments / _meta before forwarding.
_AUTH_SPOOF_KEYS = frozenset(
    {
        "authorization",
        "Authorization",
        "actor_claims",
        "claims",
        "access_token",
        "bearer",
        "token",
    }
)


def _canary_enabled(environ: Mapping[str, str]) -> bool:
    flag = str(environ.get(CANARY_ENV) or "").strip().lower()
    return flag in {"1", "true", "yes"}


def _truthy(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _strip_auth_from_mapping(value: Any) -> Any:
    """Return a copy of mapping/list structures without auth/secret keys."""
    if isinstance(value, Mapping):
        return {
            k: _strip_auth_from_mapping(v)
            for k, v in value.items()
            if k not in _AUTH_SPOOF_KEYS
        }
    if isinstance(value, list):
        return [_strip_auth_from_mapping(item) for item in value]
    return value


def _resolve_upstream(environ: Mapping[str, str]) -> str:
    """Resolve MCP upstream; production defaults to durable HTTP Gateway."""
    raw = str(environ.get(ENV_UPSTREAM) or "").strip().lower()
    if not raw:
        # Prefer HTTP durable Gateway whenever auth is not explicit local-test.
        # Avoids silent in-process + in-memory under LINKSKILLS_AUTH_MODE=production.
        if resolve_auth_mode(environ) == AUTH_MODE_LOCAL_TEST:
            return UPSTREAM_IN_PROCESS
        return UPSTREAM_HTTP
    if raw in {UPSTREAM_IN_PROCESS, UPSTREAM_HTTP}:
        return raw
    raise PaciConfigError(
        f"Unknown {ENV_UPSTREAM}={raw!r}; expected "
        f"'{UPSTREAM_IN_PROCESS}' or '{UPSTREAM_HTTP}'"
    )


def _refuse_static_bearer_for_canary(environ: Mapping[str, str]) -> None:
    """Canary must not use static bearer env (PACI machine-token only)."""
    if not _canary_enabled(environ):
        return
    static = (
        str(environ.get("LINKSKILLS_CANARY_AUTHORIZATION") or "").strip()
        or str(environ.get("GATEWAY_TOKEN") or "").strip()
        or str(environ.get("LINKSKILLS_LOCAL_TEST_STATIC_BEARER") or "").strip()
    )
    if static:
        raise SystemExit(
            "LINKSKILLS_CANARY refuses static bearer env "
            "(LINKSKILLS_CANARY_AUTHORIZATION / GATEWAY_TOKEN / "
            "LINKSKILLS_LOCAL_TEST_STATIC_BEARER); use PACI machine-token path "
            "via linkskills_mcp.paci_stdio_proxy"
        )


def require_durable_inprocess_production(environ: Mapping[str, str]) -> None:
    """Fail closed: production in-process must not silently use in-memory store.

    Requires all of:
    - ``LINKSKILLS_MCP_ALLOW_INPROCESS_PRODUCTION=1``
    - ``LINKSKILLS_ENV`` in stage/staging/production/prod
    - Gateway store resolves to ``postgres``
    - Postgres DSN present (``LINKSKILLS_DATABASE_URL`` / ``DATABASE_URL`` / …)

    Prefer ``LINKSKILLS_MCP_UPSTREAM=http`` + https ``GATEWAY_URL`` instead.
    """
    if not _truthy(environ.get(ENV_ALLOW_INPROCESS_PRODUCTION)):
        raise SystemExit(
            "LINKSKILLS_AUTH_MODE=production refuses in-process MCP Gateway "
            "(silent in-memory store is forbidden). Set "
            f"{ENV_UPSTREAM}={UPSTREAM_HTTP} with https GATEWAY_URL to the "
            "durable stage Gateway, or set "
            f"{ENV_ALLOW_INPROCESS_PRODUCTION}=1 with "
            "LINKSKILLS_ENV=stage|production, LINKSKILLS_GATEWAY_STORE=postgres, "
            "and LINKSKILLS_DATABASE_URL (or DATABASE_URL)"
        )
    if not is_production_like_env(environ):
        raise SystemExit(
            "In-process production MCP requires "
            "LINKSKILLS_ENV=stage|staging|production|prod "
            "(missing or non-production); refusing silent in-memory Gateway. "
            f"Prefer {ENV_UPSTREAM}={UPSTREAM_HTTP} with https GATEWAY_URL"
        )
    try:
        mode = resolve_gateway_store_mode(environ)
    except ValueError as exc:
        raise SystemExit(
            f"In-process production MCP store gate failed: {exc}"
        ) from exc
    if mode != "postgres":
        raise SystemExit(
            "In-process production MCP requires postgres store, "
            f"got {mode!r}; refusing silent in-memory Gateway"
        )
    if not resolve_database_dsn(environ):
        raise SystemExit(
            "In-process production MCP requires LINKSKILLS_DATABASE_URL "
            "(or DATABASE_URL / LINKSKILLS_STORE_URL / LINKSKILLS_POSTGRES_URL); "
            "refusing silent in-memory Gateway because DSN is missing"
        )


def _require_production_http_gateway_url(environ: Mapping[str, str]) -> None:
    """Production HTTP upstream must name an explicit https GATEWAY_URL."""
    url = str(environ.get("GATEWAY_URL") or "").strip()
    if not url:
        raise SystemExit(
            "LINKSKILLS_AUTH_MODE=production with "
            f"{ENV_UPSTREAM}={UPSTREAM_HTTP} requires GATEWAY_URL "
            "(https durable stage Gateway); refusing default loopback"
        )
    if not url.lower().startswith("https://"):
        raise SystemExit(
            "LINKSKILLS_AUTH_MODE=production GATEWAY_URL must be https "
            f"(got non-https); refusing non-durable upstream. "
            f"Use LINKSKILLS_AUTH_MODE=local-test only for http loopback"
        )


def build_paci_client(
    environ: Optional[Mapping[str, str]] = None,
) -> PaciTokenClient:
    """Construct Skills PACI client from env; fail closed when incomplete."""
    env = environ if environ is not None else os.environ
    mode = resolve_auth_mode(env)
    if _canary_enabled(env) and mode == AUTH_MODE_LOCAL_TEST:
        raise SystemExit(
            "LINKSKILLS_CANARY cannot use LINKSKILLS_AUTH_MODE=local-test "
            "(unsigned / static local-test path forbidden for canary)"
        )
    _refuse_static_bearer_for_canary(env)
    if not paci_env_configured(env):
        raise SystemExit(
            "PACI env incomplete for Cursor MCP proxy: require "
            "LINKSKILLS_PACI_CLIENT_ID, LINKSKILLS_PACI_TOKEN_ENDPOINT, "
            "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE"
        )
    return PaciTokenClient.from_env(env)


class PaciStdioMcpProxy:
    """Stdio JSON-RPC proxy that injects PACI Authorization server-side."""

    def __init__(
        self,
        *,
        paci_client: PaciTokenClient,
        upstream: str = UPSTREAM_HTTP,
        mcp_server: Optional[SkillsMcpServer] = None,
        gateway_client: Optional[SkillsGatewayClient] = None,
        environ: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.paci_client = paci_client
        self.upstream = upstream
        self.environ = environ if environ is not None else os.environ
        self._mcp = mcp_server
        self._gateway = gateway_client
        self._initialized = False
        self._auth_retries = 0

        mode = resolve_auth_mode(self.environ)
        if upstream == UPSTREAM_IN_PROCESS:
            # Production must never silently build an in-memory Gateway.
            if mode != AUTH_MODE_LOCAL_TEST:
                require_durable_inprocess_production(self.environ)
            if self._mcp is None:
                self._mcp = SkillsMcpServer(default_actor=None)
        elif upstream == UPSTREAM_HTTP:
            if mode != AUTH_MODE_LOCAL_TEST:
                _require_production_http_gateway_url(self.environ)
            if self._gateway is None:
                self._gateway = SkillsGatewayClient.from_env(
                    self.environ,
                    paci_client=paci_client,
                )
        else:
            raise PaciConfigError(f"Unsupported upstream mode: {upstream!r}")

    def status(self) -> Dict[str, Any]:
        """Safe diagnostics — never includes tokens or key material."""
        payload: Dict[str, Any] = {
            "proxy": "paci_stdio",
            "upstream": self.upstream,
            "canary": _canary_enabled(self.environ),
            "auth_mode": resolve_auth_mode(self.environ),
            "paci": self.paci_client.status(),
            "live_proven": False,
            "note": (
                "Skills-owned Cursor PACI MCP proxy implemented locally; "
                "Platform PACI issuer absent"
            ),
        }
        if self.upstream == UPSTREAM_IN_PROCESS:
            payload["inprocess_production_allowed"] = _truthy(
                self.environ.get(ENV_ALLOW_INPROCESS_PRODUCTION)
            )
        if self._gateway is not None:
            payload["gateway"] = self._gateway.status()
        return payload

    def _authorization(self, *, force_refresh: bool = False) -> str:
        return self.paci_client.authorization_header(force_refresh=force_refresh)

    def handle_rpc(self, message: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        method = message.get("method")
        req_id = message.get("id", None)
        params = message.get("params") or {}

        def result(payload: Any) -> Dict[str, Any]:
            return {"jsonrpc": "2.0", "id": req_id, "result": payload}

        def error(code: int, msg: str, data: Any = None) -> Dict[str, Any]:
            err: Dict[str, Any] = {"code": code, "message": msg}
            if data is not None:
                err["data"] = data
            return {"jsonrpc": "2.0", "id": req_id, "error": err}

        try:
            if method == "initialize":
                self._initialized = True
                return result(
                    {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": f"{SERVER_NAME}-paci-proxy",
                            "version": SERVER_VERSION,
                        },
                    }
                )
            if method == "notifications/initialized":
                return None
            if method == "ping":
                return result({})
            if method == "tools/list":
                return result({"tools": self._list_tools()})
            if method == "linkskills/paci_status":
                # Diagnostics only — no secrets.
                return result(self.status())
            if method == "tools/call":
                return result(self._call_tool(params if isinstance(params, Mapping) else {}))
            if req_id is None:
                return None
            return error(-32601, f"Method not found: {method}")
        except (PaciAuthError, PaciConfigError) as exc:
            logger.error("PACI MCP proxy auth fail-closed: %s", type(exc).__name__)
            if req_id is None:
                return None
            return error(-32001, str(exc), {"code": "paci_auth_failed"})
        except PaciTransientError as exc:
            logger.error("PACI MCP proxy transient failure: %s", type(exc).__name__)
            if req_id is None:
                return None
            return error(-32002, str(exc), {"code": "paci_transient_failed"})
        except PaciTokenError as exc:
            logger.error("PACI MCP proxy token failure: %s", type(exc).__name__)
            if req_id is None:
                return None
            return error(-32001, str(exc), {"code": "paci_token_failed"})
        except AuthError as exc:
            logger.error("PACI MCP proxy upstream auth fail-closed: %s", exc.code)
            if req_id is None:
                return None
            return error(-32001, exc.message, {"code": exc.code})
        except Exception as exc:  # noqa: BLE001 — boundary
            # Never include request params (may have been stripped but be cautious).
            logger.error("PACI MCP proxy internal error: %s", type(exc).__name__)
            if req_id is None:
                return None
            return error(-32603, f"Internal error: {type(exc).__name__}")

    def _list_tools(self) -> Any:
        if self.upstream == UPSTREAM_IN_PROCESS:
            assert self._mcp is not None
            return self._mcp.list_tools()
        return [_tool_schema(op) for op in OPERATIONS]

    def _call_tool(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        name = str(params.get("name") or "")
        raw_arguments = params.get("arguments") or {}
        # Strip any caller-supplied auth — proxy injects PACI bearer server-side.
        arguments = _strip_auth_from_mapping(
            raw_arguments if isinstance(raw_arguments, Mapping) else {}
        )
        if not isinstance(arguments, dict):
            arguments = {}

        if self.upstream == UPSTREAM_HTTP:
            return self._call_tool_http(name, arguments)

        return self._call_tool_in_process(name, arguments)

    def _call_tool_in_process(
        self,
        name: str,
        arguments: Dict[str, Any],
        *,
        _auth_retries: int = 0,
    ) -> Dict[str, Any]:
        assert self._mcp is not None
        authorization = self._authorization(force_refresh=_auth_retries > 0)
        try:
            envelope = self._mcp.call_tool(
                name,
                arguments,
                authorization=authorization,
            )
        except AuthError as exc:
            # Bounded 401-style invalidation: remint once then fail closed.
            if _auth_retries < 1 and exc.code in {
                "auth_expired",
                "auth_invalid",
                "auth_unsigned_rejected",
                "auth_forbidden",
            }:
                self.paci_client.invalidate()
                return self._call_tool_in_process(
                    name,
                    arguments,
                    _auth_retries=_auth_retries + 1,
                )
            raise

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(envelope, sort_keys=True),
                }
            ],
            "structuredContent": envelope,
            "isError": envelope.get("error") is not None,
        }

    def _call_tool_http(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        assert self._gateway is not None
        params = arguments.get("params") if isinstance(arguments.get("params"), dict) else {
            k: v
            for k, v in arguments.items()
            if k not in {"params", "idempotency_key", "request_id"}
        }
        envelope = self._gateway.call(
            name,
            params if isinstance(params, Mapping) else {},
            request_id=str(arguments.get("request_id") or uuid.uuid4()),
            idempotency_key=arguments.get("idempotency_key"),
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(envelope, sort_keys=True),
                }
            ],
            "structuredContent": envelope,
            "isError": envelope.get("error") is not None,
        }

    def serve_stdio(
        self,
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None,
    ) -> None:
        """Newline-delimited JSON-RPC over stdio for project-scoped Cursor MCP."""
        inn = stdin or sys.stdin
        out = stdout or sys.stdout
        for line in inn:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                out.write(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {"code": -32700, "message": "Parse error"},
                        }
                    )
                    + "\n"
                )
                out.flush()
                continue
            response = self.handle_rpc(message)
            if response is not None:
                # Never log response bodies (may embed gateway data).
                out.write(json.dumps(response, sort_keys=True) + "\n")
                out.flush()


def main(environ: Optional[Mapping[str, str]] = None) -> None:
    env = environ if environ is not None else os.environ
    try:
        paci = build_paci_client(env)
        upstream = _resolve_upstream(env)
        # Eager mint to fail closed before Cursor sends tools/call.
        paci.get_access_token()
        status = paci.status()
        logger.info(
            "linkskills PACI MCP proxy ready upstream=%s needs_renewal=%s "
            "live_proven=%s",
            upstream,
            status.get("needs_renewal"),
            status.get("live_proven"),
        )
        PaciStdioMcpProxy(
            paci_client=paci,
            upstream=upstream,
            environ=env,
        ).serve_stdio()
    except SystemExit:
        raise
    except (PaciAuthError, PaciConfigError, PaciTransientError, PaciTokenError) as exc:
        print(
            f"linkskills-mcp-paci auth fail-closed: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    except Exception as exc:  # noqa: BLE001 — boundary
        print(
            f"linkskills-mcp-paci fail-closed: {type(exc).__name__}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
