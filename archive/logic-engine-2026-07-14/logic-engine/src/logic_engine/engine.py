from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from .config import Settings
from .registry import build_registry_snapshot, load_registry_snapshot, write_registry_snapshot
from .security import SecretResolutionError, issue_disclosure_token, resolve_token_secret
from .store import AuthenticationError, JsonStore, StoreError
from .types import (
    AuditEvent,
    CapabilityClass,
    CapabilityContract,
    DisclosureIssueRequest,
    DisclosureIssueResponse,
    ExecutionReceipt,
    KillSwitchLevel,
    KillSwitchScopeType,
    OpsDashboard,
    OpsSLOSummary,
    RequestOrigin,
    RetentionClass,
    RunCreateRequest,
    RunCreateResponse,
    RunRecord,
    RunStatus,
)

DPR_PATTERN = re.compile(
    r"^(?:DPRV3-[A-Z0-9]{8,64}|INT-[A-Z]{3}-\d{6}-[A-Z0-9]{4}-[A-Z0-9-]+)$"
)


@dataclass(frozen=True)
class AuthContext:
    tenant_id: str
    principal_id: str
    key_id: str


class EngineError(RuntimeError):
    """Logic engine operation failure."""


class EngineAuthError(EngineError):
    """Auth operation failure."""


class EngineConflictError(EngineError):
    """Conflict operation failure."""


class LogicEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = JsonStore(settings)
        self._catalog_loaded = False

    def bootstrap_catalog(self) -> None:
        if self._catalog_loaded:
            return

        manifest_path = self.settings.repo_root / "manifest.json"
        result = build_registry_snapshot(self.settings.repo_root, manifest_path, self.settings.packages_path)
        write_registry_snapshot(result.snapshot, self.settings.catalog_path)
        loaded = load_registry_snapshot(self.settings.catalog_path)
        self.store.set_catalog(loaded)
        self._catalog_loaded = True

    def authenticate(self, api_key: str, source: str) -> AuthContext:
        try:
            record = self.store.authenticate_api_key(api_key, source)
        except AuthenticationError as exc:
            raise EngineAuthError(str(exc)) from exc
        return AuthContext(tenant_id=record.tenant_id, principal_id=record.principal_id, key_id=record.key_id)

    def _audit(
        self,
        *,
        tenant_id: str,
        principal_id: str,
        action: str,
        target_id: str,
        status: str,
        details: Dict[str, object],
    ) -> str:
        event = AuditEvent(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            created_at=datetime.now(timezone.utc).isoformat(),
            tenant_id=tenant_id,
            principal_id=principal_id,
            action=action,
            target_id=target_id,
            status=status,
            details=details,
        )
        self.store.append_audit(event)
        return event.event_id

    def _resolve_execution_secret(self) -> str:
        try:
            secret = resolve_token_secret(self.settings)
        except SecretResolutionError as exc:
            if self.settings.is_production:
                self.store.set_safe_mode(True, f"gsm_unavailable:{exc}")
                raise EngineError("Execution unavailable: GSM read failure in production (safe mode active)") from exc
            raise EngineError(f"Execution secret unavailable: {exc}") from exc

        if self.settings.is_production and self.store.is_safe_mode():
            # Recover automatically once GSM starts working again.
            self.store.set_safe_mode(False, None)
        return secret

    def _ensure_execution_allowed(self) -> str:
        if self.store.is_safe_mode() and self.settings.is_production:
            raise EngineError("Execution denied: service is in controlled safe mode")
        return self._resolve_execution_secret()

    def list_skill_catalog(self) -> List[CapabilityContract]:
        self.bootstrap_catalog()
        return self.store.list_capabilities(source_type="skill")

    def list_package_catalog(self):
        self.bootstrap_catalog()
        return self.store.list_packages()

    def get_skill(self, skill_id: str) -> CapabilityContract:
        self.bootstrap_catalog()
        capability = self.store.get_capability(skill_id)
        if capability.source_type.value != "skill":
            raise EngineError(f"Capability {skill_id} is not a skill")
        return capability

    def get_safe_mode_state(self) -> Dict[str, object]:
        return self.store.safe_mode_state()

    def get_slo_summary(self) -> OpsSLOSummary:
        return self.store.measure_slo()

    def get_ops_dashboard(self) -> OpsDashboard:
        return self.store.dashboard()

    def _validate_auth_binding(self, request_tenant: str, request_principal: str, auth: AuthContext) -> None:
        if request_tenant != auth.tenant_id:
            raise EngineAuthError("tenant_id does not match authenticated API key binding")
        if request_principal != auth.principal_id:
            raise EngineAuthError("principal_id does not match authenticated API key binding")

    def _resolve_capability_from_request(self, request: RunCreateRequest) -> CapabilityContract:
        if request.capability_id:
            return self.store.resolve_capability_for_tenant(request.capability_id, request.tenant_id, request.version)

        package = self.store.get_package(request.package_id or "", request.version)
        if not package.step_order:
            raise EngineError(f"Package {package.package_id} has no step_order")
        first_capability = package.step_order[0]
        return self.store.resolve_capability_for_tenant(first_capability, request.tenant_id)

    def _enforce_dpr(self, request: RunCreateRequest) -> None:
        if request.origin != RequestOrigin.AIOS:
            return
        assert request.dpr_id is not None
        if not DPR_PATTERN.match(request.dpr_id):
            raise EngineError("dpr_id failed supported format validation")
        if not self.store.validate_dpr_registry(request.dpr_id, request.tenant_id):
            raise EngineError("dpr_id not active in DPR registry for tenant")

    def _enforce_capability_policy(self, capability: CapabilityContract, tenant_id: str, run_id: str | None = None) -> None:
        policy = self.store.get_capability_policy(capability.capability_id, capability.version)

        if capability.lifecycle_state.value == "deprecated":
            raise EngineError("Capability lifecycle is deprecated")
        if capability.visibility.value != "internal":
            raise EngineError("Capability visibility is not internal")

        if policy.capability_class == CapabilityClass.CLASS_B:
            entitled = self.store.class_b_entitled(tenant_id, capability.capability_id)
            if not entitled:
                raise EngineError("Class B STUDIO_PROPRIETARY entitlement missing or override not approved")
            raise EngineError("Class B is scaffolded but not active for MVO")

        if policy.capability_class == CapabilityClass.CLASS_C:
            raise EngineError("Class C is out of MVO scope")

        if run_id:
            self.store.add_policy_decision(
                run_id,
                {
                    "check": "class_policy",
                    "result": "allow",
                    "capability_class": policy.capability_class.value,
                },
            )

    def create_run(self, request: RunCreateRequest, auth: AuthContext) -> RunCreateResponse:
        self.bootstrap_catalog()
        self._validate_auth_binding(request.tenant_id, request.principal_id, auth)

        if request.mode.value != "MANAGED":
            raise EngineError("Only MANAGED mode is allowed in MVO")

        self._ensure_execution_allowed()

        self.store.ensure_principal(request.tenant_id, request.principal_id)

        self._enforce_dpr(request)

        capability = self._resolve_capability_from_request(request)
        self._enforce_capability_policy(capability, request.tenant_id)

        self.store.enforce_new_run_allowed(request.tenant_id, capability.capability_id)

        if not self.store.principal_allowed(request.principal_id, capability.capability_id):
            raise EngineError("Principal is not entitled to this capability")

        run = self.store.create_run(
            tenant_id=request.tenant_id,
            principal_id=request.principal_id,
            capability_id=capability.capability_id,
            version=capability.version,
            context_refs=request.context_refs,
            input_payload=request.input_payload,
            mission_id=request.mission_id,
            task_id=request.task_id,
            dpr_id=request.dpr_id,
            billing_track=request.billing_track,
            venture_id=request.venture_id,
            client_id=request.client_id,
        )
        self.store.add_policy_decision(run.run_id, {"check": "tenant_entitlement", "result": "allow"})
        self.store.add_policy_decision(run.run_id, {"check": "capability_lifecycle", "result": "allow"})
        self.store.add_policy_decision(run.run_id, {"check": "execution_mode", "result": "allow", "mode": "MANAGED"})

        self._audit(
            tenant_id=request.tenant_id,
            principal_id=request.principal_id,
            action="run.create",
            target_id=run.run_id,
            status="success",
            details={
                "capability_id": capability.capability_id,
                "version": capability.version,
                "origin": request.origin.value,
                "idempotency_key": request.idempotency_key,
            },
        )

        return RunCreateResponse(
            run_id=run.run_id,
            status=RunStatus.AWAITING_DISCLOSURE,
            disclosure_required=True,
            next_action="POST /v1/disclosures/issue",
        )

    def _finalize_run_execution(self, run_id: str, receipt_id: str) -> RunRecord:
        run = self.store.get_run(run_id)
        self.store.enforce_inflight_policy(run)

        payload = self.store.get_run_input_payload(run_id)

        cost = self.store.calculate_run_cost(run.capability_id, run.version, payload)
        self.store.attach_cost_breakdown(run_id, cost)

        evidence_hashes: List[str] = []
        retention_class = RetentionClass.SUCCESS_METADATA_ONLY

        if bool(payload.get("force_error")):
            diagnostic_hash = self.store.store_failure_diagnostics(run_id, "ManagedExecutionError", "forced error")
            self.store.set_run_status(run_id, RunStatus.EVALUATION_FAILED, "ManagedExecutionError")
            evidence_hashes.append(diagnostic_hash)
            retention_class = RetentionClass.FAILURE_REDACTED_30D
        else:
            managed_output = {
                "capability_id": run.capability_id,
                "version": run.version,
                "processed_context_refs": run.context_refs,
                "summary": "Managed execution completed",
            }
            output_hash = self.store.store_success_output(run_id, managed_output)
            self.store.set_run_status(run_id, RunStatus.COMPLETED)
            evidence_hashes.append(output_hash)

        final_run = self.store.get_run(run_id)
        self.store.write_financial_ledger(final_run, cost)

        confidence = float(payload.get("eval_confidence", 1.0 if final_run.status == RunStatus.COMPLETED else 0.0))
        critical_failure = bool(payload.get("critical_failure", False))
        self.store.record_evaluation(
            run_id=run_id,
            capability_id=run.capability_id,
            version=run.version,
            confidence=confidence,
            critical_failure=critical_failure,
        )

        receipt = ExecutionReceipt(
            receipt_id=receipt_id,
            run_id=run_id,
            result_status=final_run.status,
            policy_summary=final_run.policy_decisions,
            retention_class=retention_class,
            evidence_hashes=evidence_hashes,
            data_purge_status="scheduled",
            created_at=datetime.now(timezone.utc).isoformat(),
            purge_due_at=(datetime.now(timezone.utc) + timedelta(days=180)).isoformat(),
            cost_breakdown=cost,
            audit_refs=[],
        )
        self.store.save_receipt(receipt)

        self.store.evaluate_level2_triggers()
        return final_run

    def _maybe_finalize_pending(self, run_id: str) -> None:
        tick = self.store.tick_pending_execution(run_id)
        if not tick:
            return
        if not bool(tick.get("ready", False)):
            return
        receipt_id = str(tick.get("receipt_id"))
        self._finalize_run_execution(run_id, receipt_id)

    def get_run(self, run_id: str) -> RunRecord:
        self._maybe_finalize_pending(run_id)
        return self.store.get_run(run_id)

    def issue_disclosure(self, request: DisclosureIssueRequest, auth: AuthContext) -> DisclosureIssueResponse:
        token_secret = self._ensure_execution_allowed()
        run = self.store.get_run(request.run_id)

        if run.tenant_id != auth.tenant_id or run.principal_id != auth.principal_id:
            raise EngineAuthError("run ownership does not match authenticated API key binding")

        if run.status != RunStatus.AWAITING_DISCLOSURE:
            if run.status == RunStatus.IN_PROGRESS:
                existing = self.store.get_receipt_for_run(run.run_id)
                if existing:
                    return DisclosureIssueResponse(
                        disclosure_token="",
                        expires_at=datetime.now(timezone.utc).isoformat(),
                        manifest_ref="",
                        run_status=run.status,
                        receipt_id=existing.receipt_id,
                        terminal=False,
                    )
            raise EngineError("Run is not awaiting disclosure")

        capability = self.store.get_capability(run.capability_id, run.version)
        self._enforce_capability_policy(capability, run.tenant_id, run.run_id)

        token, claims = issue_disclosure_token(
            secret=token_secret,
            tenant_id=run.tenant_id,
            run_id=run.run_id,
            capability_id=run.capability_id,
            version=run.version,
            step_scope=request.step_scope,
            ttl_seconds=self.settings.token_ttl_seconds,
        )

        manifest_ref = f"manifest-{run.run_id}-{claims.jti[:8]}"
        self.store.save_disclosure(
            run_id=run.run_id,
            tenant_id=run.tenant_id,
            principal_id=run.principal_id,
            step_scope=request.step_scope,
            token_jti=claims.jti,
            token_exp=claims.exp,
            manifest_ref=manifest_ref,
        )
        self.store.add_policy_decision(run.run_id, {"check": "run_state_compatibility", "result": "allow"})
        self.store.set_run_status(run.run_id, RunStatus.IN_PROGRESS)

        payload = self.store.get_run_input_payload(run.run_id)
        simulated_duration = float(payload.get("simulate_duration_seconds", 0) or 0)
        pending_receipt_id = f"rcpt-{uuid.uuid4().hex[:12]}"

        terminal = True
        if simulated_duration > float(self.settings.execution_timeout_seconds):
            terminal = False
            self.store.set_pending_execution(
                run.run_id,
                pending_polls=int(payload.get("pending_polls", 1) or 1),
                receipt_id=pending_receipt_id,
                step_scope=request.step_scope,
                manifest_ref=manifest_ref,
                token_jti=claims.jti,
            )
            pending_receipt = ExecutionReceipt(
                receipt_id=pending_receipt_id,
                run_id=run.run_id,
                result_status=RunStatus.IN_PROGRESS,
                policy_summary=run.policy_decisions,
                retention_class=RetentionClass.DISCLOSURE_AUDIT_180D,
                evidence_hashes=[],
                data_purge_status="pending",
                created_at=datetime.now(timezone.utc).isoformat(),
                purge_due_at=(datetime.now(timezone.utc) + timedelta(days=180)).isoformat(),
                cost_breakdown=None,
                audit_refs=[],
            )
            self.store.save_receipt(pending_receipt)
        else:
            self._finalize_run_execution(run.run_id, pending_receipt_id)

        final_run = self.store.get_run(run.run_id)
        final_receipt = self.store.get_receipt_for_run(run.run_id)
        if final_receipt is None:
            raise EngineError("Receipt creation failed")

        audit_id = self._audit(
            tenant_id=run.tenant_id,
            principal_id=run.principal_id,
            action="disclosure.issue",
            target_id=run.run_id,
            status="success",
            details={
                "manifest_ref": manifest_ref,
                "token_exp": claims.exp,
                "receipt_id": final_receipt.receipt_id,
                "terminal": terminal,
                "idempotency_key": request.idempotency_key,
            },
        )

        final_receipt.audit_refs.append(audit_id)
        self.store.save_receipt(final_receipt)

        expires_at = datetime.fromtimestamp(claims.exp, tz=timezone.utc).isoformat()
        return DisclosureIssueResponse(
            disclosure_token=token,
            expires_at=expires_at,
            manifest_ref=manifest_ref,
            run_status=final_run.status,
            receipt_id=final_receipt.receipt_id,
            terminal=terminal,
        )

    def get_receipt(self, receipt_id: str) -> ExecutionReceipt:
        receipt = self.store.get_receipt(receipt_id)
        self._maybe_finalize_pending(receipt.run_id)
        return self.store.get_receipt(receipt_id)

    def run_retention_sweep(self):
        return self.store.retention_sweep()
