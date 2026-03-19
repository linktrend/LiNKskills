from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from .config import load_settings
from .engine import AuthContext, EngineAuthError, EngineConflictError, EngineError, LogicEngine
from .security import hash_payload
from .store import IdempotencyConflictError
from .types import DisclosureIssueRequest, RunCreateRequest, UsageEvent


def create_app() -> FastAPI:
    settings = load_settings()
    engine = LogicEngine(settings)

    app = FastAPI(title="LiNKskills Logic Engine", version="0.4.0")

    def _raise_engine_error(exc: Exception) -> None:
        message = str(exc)
        if isinstance(exc, EngineAuthError):
            raise HTTPException(status_code=403, detail=message) from exc
        if isinstance(exc, EngineConflictError):
            raise HTTPException(status_code=409, detail=message) from exc
        if isinstance(exc, IdempotencyConflictError):
            raise HTTPException(status_code=409, detail=message) from exc
        if "safe mode" in message.lower() or "execution unavailable" in message.lower():
            raise HTTPException(status_code=503, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    def require_auth(
        request: Request,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> AuthContext:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization bearer token required")
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization must be a Bearer token")

        raw_key = authorization[len("Bearer ") :].strip()
        if not raw_key:
            raise HTTPException(status_code=401, detail="Bearer token is empty")

        source = request.client.host if request.client else "unknown"
        try:
            auth = engine.authenticate(raw_key, source)
        except EngineAuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        request.state.auth_context = auth
        return auth

    @app.middleware("http")
    async def usage_middleware(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        if request.url.path.startswith("/v1/"):
            auth = getattr(request.state, "auth_context", None)
            if auth is not None:
                usage = UsageEvent(
                    event_id=f"use-{uuid.uuid4().hex[:12]}",
                    created_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    tenant_id=auth.tenant_id,
                    principal_id=auth.principal_id,
                    action=request.method,
                    endpoint=request.url.path,
                    latency_ms=elapsed_ms,
                    success=response.status_code < 500,
                    dimensions={"status_code": response.status_code},
                )
                engine.store.record_usage(usage)

        return response

    @app.get("/health")
    def health() -> dict[str, Any]:
        safe_mode = engine.get_safe_mode_state()
        return {
            "status": "ok",
            "service": "logic-engine",
            "phase": "0-3",
            "safe_mode": safe_mode,
        }

    @app.get("/v1/catalog/skills")
    def catalog_skills(_: AuthContext = Depends(require_auth)) -> list[dict[str, object]]:
        try:
            items = engine.list_skill_catalog()
            return [item.model_dump(mode="json") for item in items]
        except Exception as exc:
            _raise_engine_error(exc)

    @app.get("/v1/catalog/packages")
    def catalog_packages(_: AuthContext = Depends(require_auth)) -> list[dict[str, object]]:
        try:
            items = engine.list_package_catalog()
            return [item.model_dump(mode="json") for item in items]
        except Exception as exc:
            _raise_engine_error(exc)

    @app.get("/v1/skills/{skill_id}")
    def get_skill(skill_id: str, _: AuthContext = Depends(require_auth)) -> dict[str, object]:
        try:
            skill = engine.get_skill(skill_id)
            return skill.model_dump(mode="json")
        except Exception as exc:
            _raise_engine_error(exc)

    @app.post("/v1/runs")
    def create_run(payload: RunCreateRequest, auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        dedupe_hash = hash_payload(payload.model_dump(mode="json", exclude={"idempotency_key"}))
        try:
            replay = engine.store.claim_idempotency(
                endpoint="/v1/runs",
                tenant_id=auth.tenant_id,
                principal_id=auth.principal_id,
                idempotency_key=payload.idempotency_key,
                payload_hash=dedupe_hash,
            )
            if replay is not None:
                replay["idempotent_replay"] = True
                return replay

            response = engine.create_run(payload, auth)
            body = response.model_dump(mode="json")
            engine.store.store_idempotency_response(
                endpoint="/v1/runs",
                tenant_id=auth.tenant_id,
                principal_id=auth.principal_id,
                idempotency_key=payload.idempotency_key,
                payload_hash=dedupe_hash,
                response_payload=body,
                status_code=200,
            )
            return body
        except Exception as exc:
            _raise_engine_error(exc)

    @app.get("/v1/runs/{run_id}")
    def get_run(run_id: str, auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        try:
            run = engine.get_run(run_id)
            if run.tenant_id != auth.tenant_id or run.principal_id != auth.principal_id:
                raise EngineAuthError("run access denied for authenticated principal")
            return run.model_dump(mode="json")
        except Exception as exc:
            _raise_engine_error(exc)

    @app.post("/v1/disclosures/issue")
    def issue_disclosure(payload: DisclosureIssueRequest, auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        dedupe_hash = hash_payload(payload.model_dump(mode="json", exclude={"idempotency_key"}))
        try:
            replay = engine.store.claim_idempotency(
                endpoint="/v1/disclosures/issue",
                tenant_id=auth.tenant_id,
                principal_id=auth.principal_id,
                idempotency_key=payload.idempotency_key,
                payload_hash=dedupe_hash,
            )
            if replay is not None:
                replay["idempotent_replay"] = True
                return replay

            response = engine.issue_disclosure(payload, auth)
            body = response.model_dump(mode="json")
            engine.store.store_idempotency_response(
                endpoint="/v1/disclosures/issue",
                tenant_id=auth.tenant_id,
                principal_id=auth.principal_id,
                idempotency_key=payload.idempotency_key,
                payload_hash=dedupe_hash,
                response_payload=body,
                status_code=200,
            )
            return body
        except Exception as exc:
            _raise_engine_error(exc)

    @app.get("/v1/receipts/{receipt_id}")
    def get_receipt(receipt_id: str, auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        try:
            receipt = engine.get_receipt(receipt_id)
            run = engine.get_run(receipt.run_id)
            if run.tenant_id != auth.tenant_id or run.principal_id != auth.principal_id:
                raise EngineAuthError("receipt access denied for authenticated principal")
            return receipt.model_dump(mode="json")
        except Exception as exc:
            _raise_engine_error(exc)

    @app.get("/v1/ops/slo")
    def ops_slo(_: AuthContext = Depends(require_auth)) -> dict[str, object]:
        try:
            return engine.get_slo_summary().model_dump(mode="json")
        except Exception as exc:
            _raise_engine_error(exc)

    @app.get("/v1/ops/dashboard")
    def ops_dashboard(_: AuthContext = Depends(require_auth)) -> dict[str, object]:
        try:
            return engine.get_ops_dashboard().model_dump(mode="json")
        except Exception as exc:
            _raise_engine_error(exc)

    @app.get("/v1/ops/safe-mode")
    def ops_safe_mode(_: AuthContext = Depends(require_auth)) -> dict[str, object]:
        return engine.get_safe_mode_state()

    return app
