from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import Settings
from .security import hash_api_key, resolve_named_secret
from .types import (
    ApiKeyRecord,
    ApiKeyState,
    AuditEvent,
    BillingTrack,
    CapabilityClass,
    CapabilityContract,
    CapabilityVersionPolicy,
    CatalogSnapshot,
    ComplexityMultiplierRecord,
    ExecutionReceipt,
    FinancialLedgerEntry,
    IdempotencyRecord,
    KillSwitchLevel,
    KillSwitchScopeType,
    KillSwitchState,
    LicenseType,
    OpsDashboard,
    OpsSLOSummary,
    PackageContract,
    RetentionClass,
    RetentionSweepResult,
    RunCostBreakdown,
    RunRecord,
    RunStatus,
    SecurityEvent,
    UsageEvent,
)


class StoreError(RuntimeError):
    """Store operation failure."""


class IdempotencyConflictError(StoreError):
    """Idempotency key was reused with a different payload."""


class AuthenticationError(StoreError):
    """Service API key authentication failed."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _utc_now().isoformat()


def _semantic_key(version: str) -> tuple:
    parts = version.split(".")
    parsed: List[int | str] = []
    for part in parts:
        try:
            parsed.append(int(part))
        except ValueError:
            parsed.append(part)
    return tuple(parsed)


def _hash_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise StoreError(f"Failed to parse JSON file {path}: {exc}") from exc


def _month_bounds(ts: datetime) -> Tuple[datetime, datetime]:
    start = ts.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def _to_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _five_minute_bucket(ts: datetime) -> str:
    minute = ts.minute - (ts.minute % 5)
    return ts.replace(minute=minute, second=0, microsecond=0).isoformat()


class JsonStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.data_path = settings.data_path
        self._state = self._load()
        self._state.setdefault(
            "tenants",
            {
                settings.internal_tenant_default: {
                    "tenant_id": settings.internal_tenant_default,
                    "slug": settings.internal_tenant_slug,
                    "kind": "internal",
                    "created_at": _now_iso(),
                }
            },
        )
        self._state.setdefault("principals", {})
        self._state.setdefault("catalog", {"capabilities": [], "packages": []})
        self._state.setdefault("runs", {})
        self._state.setdefault("receipts", {})
        self._state.setdefault("disclosures", {})
        self._state.setdefault("audit_logs", [])
        self._state.setdefault("usage_events", [])
        self._state.setdefault("security_events", [])
        self._state.setdefault("financial_ledger", [])
        self._state.setdefault("idempotency", {})
        self._state.setdefault("api_keys", {})
        self._state.setdefault("kill_switch", KillSwitchState().model_dump(mode="json"))
        self._state.setdefault("safe_mode", {"enabled": False, "reason": None, "updated_at": None})
        self._state.setdefault("alerts", [])
        self._state.setdefault("protection_state", {"projected_over_cap_streak": 0, "last_projected_bucket": None})
        self._state.setdefault("evaluation_history", [])
        self._state.setdefault("rollback_actions", [])
        self._state.setdefault("purge_confirmations", [])
        self._state.setdefault("references", {})

        self._load_reference_data()
        self._bootstrap_api_keys()
        self._persist()

    def _load(self) -> Dict[str, Any]:
        if not self.data_path.exists():
            return {}
        return json.loads(self.data_path.read_text(encoding="utf-8"))

    def _persist(self) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.data_path.write_text(json.dumps(self._state, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def _load_reference_data(self) -> None:
        refs = self._state["references"]

        dpr_data = _load_json(self.settings.dpr_registry_path, {"records": []})
        refs["dpr_registry"] = self._normalize_records_payload(dpr_data)

        policy_data = _load_json(self.settings.capability_policy_path, {"records": []})
        refs["capability_policy"] = self._normalize_records_payload(policy_data)

        complexity_data = _load_json(self.settings.complexity_path, {"records": []})
        refs["complexity_multipliers"] = self._normalize_records_payload(complexity_data)

        provider_pricing_data = _load_json(
            self.settings.provider_pricing_path,
            {
                "default_model": "default",
                "models": {"default": {"input_per_1k": 0.0, "output_per_1k": 0.0}},
                "tool_pricing": {},
            },
        )
        refs["provider_pricing"] = provider_pricing_data

        class_b_entitlements = _load_json(self.settings.class_b_entitlements_path, {"records": []})
        refs["class_b_entitlements"] = self._normalize_records_payload(class_b_entitlements)

        override_approvals = _load_json(self.settings.override_approvals_path, {"records": []})
        refs["override_approvals"] = self._normalize_records_payload(override_approvals)

    @staticmethod
    def _normalize_records_payload(payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            records = payload.get("records", [])
            if isinstance(records, list):
                return [item for item in records if isinstance(item, dict)]
        return []

    def _bootstrap_api_keys(self) -> None:
        key_rows = _load_json(self.settings.api_keys_path, {"records": []})
        key_records = self._normalize_records_payload(key_rows)

        if not key_records:
            key_records = [
                {
                    "key_id": "bootstrap-internal",
                    "api_key": self.settings.bootstrap_api_key,
                    "tenant_id": self.settings.internal_tenant_default,
                    "principal_id": "linktrend-internal-agent",
                    "state": "active",
                    "metadata": {"bootstrap": True},
                }
            ]

        for row in key_records:
            raw_key = str(row.get("api_key", "")).strip()
            key_hash = str(row.get("key_hash", "")).strip()
            secret_name = str(row.get("secret_name", "")).strip()
            if not key_hash:
                if not raw_key and secret_name:
                    raw_key = resolve_named_secret(self.settings, secret_name)
                if not raw_key:
                    raise StoreError("API key record requires key_hash, api_key, or secret_name")
                key_hash = hash_api_key(raw_key)

            entry = ApiKeyRecord(
                key_id=str(row.get("key_id", f"key-{key_hash[:12]}")),
                key_hash=key_hash,
                tenant_id=str(row.get("tenant_id", self.settings.internal_tenant_default)),
                principal_id=str(row.get("principal_id", "linktrend-internal-agent")),
                state=ApiKeyState(str(row.get("state", "active"))),
                created_at=str(row.get("created_at", _now_iso())),
                rotated_at=row.get("rotated_at"),
                revoked_at=row.get("revoked_at"),
                last_used_at=row.get("last_used_at"),
                metadata=dict(row.get("metadata", {})),
            )
            self.ensure_principal(entry.tenant_id, entry.principal_id)
            self._state["api_keys"][entry.key_hash] = entry.model_dump(mode="json")

    def set_catalog(self, snapshot: CatalogSnapshot) -> None:
        self._state["catalog"] = {
            "generated_at": snapshot.generated_at,
            "capabilities": [item.model_dump(mode="json") for item in snapshot.capabilities],
            "packages": [item.model_dump(mode="json") for item in snapshot.packages],
        }
        self._persist()

    def list_capabilities(self, source_type: str | None = None) -> List[CapabilityContract]:
        payload = self._state.get("catalog", {}).get("capabilities", [])
        items = [self._apply_policy_overlay(CapabilityContract(**row)) for row in payload]
        if source_type:
            items = [item for item in items if item.source_type.value == source_type]
        return sorted(items, key=lambda x: x.capability_id)

    def list_packages(self) -> List[PackageContract]:
        payload = self._state.get("catalog", {}).get("packages", [])
        items = [PackageContract(**row) for row in payload]
        return sorted(items, key=lambda x: x.package_id)

    def _get_policy_map(self) -> Dict[str, Dict[str, Any]]:
        records = self._state["references"].get("capability_policy", [])
        policy_map: Dict[str, Dict[str, Any]] = {}
        for row in records:
            capability_id = str(row.get("capability_id", "")).strip()
            version = str(row.get("version", "")).strip()
            if not capability_id or not version:
                continue
            policy_map[f"{capability_id}:{version}"] = row
        return policy_map

    def _apply_policy_overlay(self, capability: CapabilityContract) -> CapabilityContract:
        policy_map = self._get_policy_map()
        raw = policy_map.get(f"{capability.capability_id}:{capability.version}")
        if not raw:
            return capability

        policy = CapabilityVersionPolicy(**raw)
        updated = capability.model_copy(deep=True)
        updated.certification_state = policy.certification_state
        updated.activation_state = policy.activation_state
        updated.capability_class = policy.capability_class
        updated.license_type = policy.license_type
        updated.visibility = policy.visibility
        updated.active_from = policy.effective_from
        return updated

    def get_capability(self, capability_id: str, version: str | None = None) -> CapabilityContract:
        candidates = [item for item in self.list_capabilities() if item.capability_id == capability_id]
        if not candidates:
            raise StoreError(f"Capability not found: {capability_id}")

        if version:
            for item in candidates:
                if item.version == version:
                    return item
            raise StoreError(f"Capability {capability_id} version {version} not found")

        return sorted(candidates, key=lambda x: _semantic_key(x.version))[-1]

    def resolve_capability_for_tenant(self, capability_id: str, tenant_id: str, version: str | None = None) -> CapabilityContract:
        candidates = [item for item in self.list_capabilities() if item.capability_id == capability_id]
        if not candidates:
            raise StoreError(f"Capability not found: {capability_id}")

        if version:
            candidates = [item for item in candidates if item.version == version]
            if not candidates:
                raise StoreError(f"Capability {capability_id} version {version} not found")
        else:
            candidates = sorted(candidates, key=lambda x: _semantic_key(x.version), reverse=True)

        policies = self._get_policy_map()
        for capability in candidates:
            policy_raw = policies.get(f"{capability.capability_id}:{capability.version}")
            policy = CapabilityVersionPolicy(**policy_raw) if policy_raw else CapabilityVersionPolicy(
                capability_id=capability.capability_id,
                version=capability.version,
            )
            if policy.certification_state.value != "certified":
                continue
            if policy.activation_state.value != "active":
                continue
            if policy.visibility.value != "internal":
                continue
            if policy.capability_class != CapabilityClass.CLASS_A:
                continue
            if policy.allowed_tenants and tenant_id not in policy.allowed_tenants:
                continue
            return self._apply_policy_overlay(capability)

        raise StoreError(
            f"No certified internal active capability version available for {capability_id} in tenant {tenant_id}"
        )

    def get_package(self, package_id: str, version: str | None = None) -> PackageContract:
        candidates = [item for item in self.list_packages() if item.package_id == package_id]
        if not candidates:
            raise StoreError(f"Package not found: {package_id}")
        if version:
            for item in candidates:
                if item.version == version:
                    return item
            raise StoreError(f"Package {package_id} version {version} not found")
        return sorted(candidates, key=lambda x: _semantic_key(x.version))[-1]

    def ensure_principal(self, tenant_id: str, principal_id: str) -> None:
        principals = self._state["principals"]
        existing = principals.get(principal_id)
        if existing is None:
            principals[principal_id] = {
                "principal_id": principal_id,
                "tenant_id": tenant_id,
                "allowed_capabilities": [],
                "created_at": _now_iso(),
            }
            self._persist()
            return

        if existing.get("tenant_id") != tenant_id:
            raise StoreError(f"Principal {principal_id} does not belong to tenant {tenant_id}")

    def principal_allowed(self, principal_id: str, capability_id: str) -> bool:
        principal = self._state["principals"].get(principal_id)
        if principal is None:
            return False
        allowed = principal.get("allowed_capabilities", [])
        return not allowed or capability_id in allowed

    def authenticate_api_key(self, raw_key: str, source: str) -> ApiKeyRecord:
        key_hash = hash_api_key(raw_key)
        row = self._state["api_keys"].get(key_hash)
        if row is None:
            self.record_security_event(
                source=source,
                event_type="invalid_signature_replay",
                severity="critical",
                details={"reason": "unknown_api_key"},
            )
            raise AuthenticationError("Invalid API key")

        record = ApiKeyRecord(**row)
        if record.state != ApiKeyState.ACTIVE:
            self.record_security_event(
                source=source,
                tenant_id=record.tenant_id,
                principal_id=record.principal_id,
                event_type="invalid_signature_replay",
                severity="critical",
                details={"reason": "revoked_api_key", "key_id": record.key_id},
            )
            raise AuthenticationError("API key revoked")

        row["last_used_at"] = _now_iso()
        self._persist()
        return ApiKeyRecord(**row)

    def claim_idempotency(
        self,
        *,
        endpoint: str,
        tenant_id: str,
        principal_id: str,
        idempotency_key: str,
        payload_hash: str,
    ) -> Optional[Dict[str, Any]]:
        dedupe_scope = f"{endpoint}:{tenant_id}:{principal_id}:{idempotency_key}"
        record_row = self._state["idempotency"].get(dedupe_scope)
        if record_row is None:
            return None

        record = IdempotencyRecord(**record_row)
        if _to_datetime(record.expires_at) <= _utc_now():
            del self._state["idempotency"][dedupe_scope]
            self._persist()
            return None

        if record.payload_hash != payload_hash:
            raise IdempotencyConflictError("Same idempotency_key used with different payload")

        return dict(record.response_payload)

    def store_idempotency_response(
        self,
        *,
        endpoint: str,
        tenant_id: str,
        principal_id: str,
        idempotency_key: str,
        payload_hash: str,
        response_payload: Dict[str, Any],
        status_code: int = 200,
    ) -> None:
        dedupe_scope = f"{endpoint}:{tenant_id}:{principal_id}:{idempotency_key}"
        row = IdempotencyRecord(
            dedupe_scope=dedupe_scope,
            endpoint=endpoint,
            tenant_id=tenant_id,
            principal_id=principal_id,
            idempotency_key=idempotency_key,
            payload_hash=payload_hash,
            response_payload=response_payload,
            status_code=status_code,
            created_at=_now_iso(),
            expires_at=(_utc_now() + timedelta(hours=self.settings.idempotency_ttl_hours)).isoformat(),
        )
        self._state["idempotency"][dedupe_scope] = row.model_dump(mode="json")
        self._persist()

    def create_run(
        self,
        *,
        tenant_id: str,
        principal_id: str,
        capability_id: str,
        version: str,
        context_refs: List[str],
        input_payload: Dict[str, Any],
        mission_id: str | None,
        task_id: str | None,
        dpr_id: str | None,
        billing_track: BillingTrack,
        venture_id: str | None,
        client_id: str | None,
    ) -> RunRecord:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        run = RunRecord(
            run_id=run_id,
            tenant_id=tenant_id,
            principal_id=principal_id,
            capability_id=capability_id,
            version=version,
            status=RunStatus.AWAITING_DISCLOSURE,
            started_at=_now_iso(),
            context_refs=context_refs,
            mission_id=mission_id,
            task_id=task_id,
            dpr_id=dpr_id,
            billing_track=billing_track,
            venture_id=venture_id,
            client_id=client_id,
        )
        row = run.model_dump(mode="json")
        row["_input_payload"] = input_payload
        self._state["runs"][run_id] = row
        self._persist()
        return run

    def get_run(self, run_id: str) -> RunRecord:
        row = self._state["runs"].get(run_id)
        if row is None:
            raise StoreError(f"Run not found: {run_id}")
        payload = dict(row)
        payload.pop("_input_payload", None)
        payload.pop("_diagnostics_expire_at", None)
        payload.pop("_pending_execution", None)
        return RunRecord(**payload)

    def get_run_input_payload(self, run_id: str) -> Dict[str, Any]:
        row = self._state["runs"].get(run_id)
        if row is None:
            raise StoreError(f"Run not found: {run_id}")
        return dict(row.get("_input_payload", {}))

    def add_policy_decision(self, run_id: str, decision: Dict[str, Any]) -> None:
        row = self._state["runs"].get(run_id)
        if row is None:
            raise StoreError(f"Run not found: {run_id}")
        row.setdefault("policy_decisions", []).append(decision)
        self._persist()

    def set_run_status(self, run_id: str, status: RunStatus, error_class: str | None = None) -> None:
        row = self._state["runs"].get(run_id)
        if row is None:
            raise StoreError(f"Run not found: {run_id}")
        row["status"] = status.value
        if error_class:
            row["error_class"] = error_class
        if status in {
            RunStatus.COMPLETED,
            RunStatus.EVALUATION_FAILED,
            RunStatus.PURGED,
            RunStatus.POLICY_DENIED,
            RunStatus.CANCELLED,
        }:
            row["completed_at"] = _now_iso()
        self._persist()

    def attach_cost_breakdown(self, run_id: str, breakdown: RunCostBreakdown) -> None:
        row = self._state["runs"].get(run_id)
        if row is None:
            raise StoreError(f"Run not found: {run_id}")
        row["cost_breakdown"] = breakdown.model_dump(mode="json")
        self._persist()

    def store_success_output(self, run_id: str, output_payload: Dict[str, Any]) -> str:
        row = self._state["runs"].get(run_id)
        if row is None:
            raise StoreError(f"Run not found: {run_id}")

        serialized = json.dumps(output_payload, sort_keys=True, ensure_ascii=True)
        output_hash = _hash_text(serialized)
        row["output_metadata"] = {
            "output_hash": output_hash,
            "top_level_keys": sorted(list(output_payload.keys())),
            "captured_at": _now_iso(),
        }
        row.pop("diagnostics_redacted", None)
        row.pop("_diagnostics_expire_at", None)
        row.pop("_input_payload", None)
        self._persist()
        return output_hash

    def store_failure_diagnostics(self, run_id: str, error_class: str, message: str) -> str:
        row = self._state["runs"].get(run_id)
        if row is None:
            raise StoreError(f"Run not found: {run_id}")

        redacted = {
            "error_class": error_class,
            "message": "Execution failed. See audit and receipt hashes for traceability.",
            "captured_at": _now_iso(),
        }
        diagnostic_hash = _hash_text(json.dumps({"error_class": error_class, "message": message}, sort_keys=True))
        row["diagnostics_redacted"] = {**redacted, "diagnostic_hash": diagnostic_hash}
        row["_diagnostics_expire_at"] = (_utc_now() + timedelta(days=30)).isoformat()
        row.pop("_input_payload", None)
        self._persist()
        return diagnostic_hash

    def save_disclosure(
        self,
        *,
        run_id: str,
        tenant_id: str,
        principal_id: str,
        step_scope: str,
        token_jti: str,
        token_exp: int,
        manifest_ref: str,
    ) -> str:
        disclosure_id = f"dsc-{uuid.uuid4().hex[:12]}"
        self._state["disclosures"][disclosure_id] = {
            "disclosure_id": disclosure_id,
            "run_id": run_id,
            "tenant_id": tenant_id,
            "principal_id": principal_id,
            "step_scope": step_scope,
            "token_jti": token_jti,
            "token_exp": token_exp,
            "manifest_ref": manifest_ref,
            "created_at": _now_iso(),
            "purge_due_at": (_utc_now() + timedelta(days=180)).isoformat(),
        }
        self._persist()
        return disclosure_id

    def save_receipt(self, receipt: ExecutionReceipt) -> None:
        self._state["receipts"][receipt.receipt_id] = receipt.model_dump(mode="json")
        self._persist()

    def get_receipt(self, receipt_id: str) -> ExecutionReceipt:
        row = self._state["receipts"].get(receipt_id)
        if row is None:
            raise StoreError(f"Receipt not found: {receipt_id}")
        return ExecutionReceipt(**row)

    def append_audit(self, event: AuditEvent) -> None:
        row = event.model_dump(mode="json")
        row["purge_due_at"] = (_utc_now() + timedelta(days=180)).isoformat()
        self._state["audit_logs"].append(row)
        self._persist()

    def record_usage(self, event: UsageEvent) -> None:
        self._state["usage_events"].append(event.model_dump(mode="json"))
        self._persist()

    def record_security_event(
        self,
        *,
        source: str,
        event_type: str,
        severity: str,
        tenant_id: str | None = None,
        principal_id: str | None = None,
        details: Dict[str, Any] | None = None,
    ) -> None:
        event = SecurityEvent(
            event_id=f"sec-{uuid.uuid4().hex[:12]}",
            created_at=_now_iso(),
            source=source,
            tenant_id=tenant_id,
            principal_id=principal_id,
            event_type=event_type,
            severity=severity,
            details=details or {},
        )
        self._state["security_events"].append(event.model_dump(mode="json"))
        self._persist()

    def add_alert(self, message: str) -> None:
        alerts = self._state["alerts"]
        alerts.append({"message": message, "created_at": _now_iso()})
        self._state["alerts"] = alerts[-200:]
        self._persist()

    def get_active_alerts(self) -> List[str]:
        return [str(row.get("message", "")) for row in self._state.get("alerts", [])]

    def get_kill_switch(self) -> KillSwitchState:
        return KillSwitchState(**self._state["kill_switch"])

    def set_kill_switch(
        self,
        *,
        level: KillSwitchLevel,
        scope_type: KillSwitchScopeType,
        scope_id: str,
        reason: str,
        hard_cancel_inflight: bool,
        activated_by: str,
    ) -> None:
        self._state["kill_switch"] = KillSwitchState(
            level=level,
            scope_type=scope_type,
            scope_id=scope_id,
            reason=reason,
            hard_cancel_inflight=hard_cancel_inflight,
            activated_at=_now_iso(),
            activated_by=activated_by,
        ).model_dump(mode="json")
        self._persist()

    def _kill_switch_blocks_tenant(self, tenant_id: str, capability_id: str | None = None) -> bool:
        state = self.get_kill_switch()
        if state.level == KillSwitchLevel.LEVEL_1:
            return False
        if state.scope_type == KillSwitchScopeType.PLATFORM:
            return True
        if state.scope_type == KillSwitchScopeType.TENANT:
            return state.scope_id == tenant_id
        if state.scope_type == KillSwitchScopeType.WORKLOAD and capability_id:
            return state.scope_id == capability_id
        return False

    def enforce_new_run_allowed(self, tenant_id: str, capability_id: str) -> None:
        if self._kill_switch_blocks_tenant(tenant_id, capability_id):
            raise StoreError("Run creation halted by Level-2/3 kill switch")

    def enforce_inflight_policy(self, run: RunRecord) -> None:
        state = self.get_kill_switch()
        if state.level in {KillSwitchLevel.LEVEL_2, KillSwitchLevel.LEVEL_3} and state.hard_cancel_inflight:
            if self._kill_switch_blocks_tenant(run.tenant_id, run.capability_id):
                self.set_run_status(run.run_id, RunStatus.CANCELLED, "KillSwitchHardCancel")
                raise StoreError("In-flight run cancelled by critical kill switch")

    def set_safe_mode(self, enabled: bool, reason: str | None) -> None:
        self._state["safe_mode"] = {
            "enabled": enabled,
            "reason": reason,
            "updated_at": _now_iso(),
        }
        self._persist()

    def is_safe_mode(self) -> bool:
        return bool(self._state.get("safe_mode", {}).get("enabled", False))

    def safe_mode_state(self) -> Dict[str, Any]:
        return dict(self._state.get("safe_mode", {}))

    def validate_dpr_registry(self, dpr_id: str, tenant_id: str) -> bool:
        rows = self._state["references"].get("dpr_registry", [])
        for row in rows:
            if str(row.get("dpr_id", "")) != dpr_id:
                continue
            if not bool(row.get("active", False)):
                return False
            registered_tenant = row.get("tenant_id")
            if registered_tenant and str(registered_tenant) != tenant_id:
                return False
            return True
        return False

    def class_b_entitled(self, tenant_id: str, capability_id: str) -> bool:
        entitlements = self._state["references"].get("class_b_entitlements", [])
        for row in entitlements:
            if str(row.get("tenant_id", "")) != tenant_id:
                continue
            if str(row.get("capability_id", "")) != capability_id:
                continue
            if bool(row.get("active", False)):
                return True

        approvals = self._state["references"].get("override_approvals", [])
        for row in approvals:
            if str(row.get("tenant_id", "")) != tenant_id:
                continue
            if str(row.get("capability_id", "")) != capability_id:
                continue
            if not bool(row.get("approved", False)):
                continue

            chain = {str(item).strip().lower() for item in row.get("authority_chain", [])}
            emergency = bool(row.get("emergency", False))
            if emergency and "chairman" in chain:
                return True

            has_finance = "head_of_finance" in chain
            has_exec = "coo" in chain or "ceo" in chain
            if has_finance and has_exec:
                return True
        return False

    def get_capability_policy(self, capability_id: str, version: str) -> CapabilityVersionPolicy:
        policy = self._get_policy_map().get(f"{capability_id}:{version}")
        if policy:
            return CapabilityVersionPolicy(**policy)
        capability = self.get_capability(capability_id, version)
        return CapabilityVersionPolicy(
            capability_id=capability_id,
            version=version,
            certification_state=capability.certification_state,
            activation_state=capability.activation_state,
            capability_class=capability.capability_class,
            visibility=capability.visibility,
            license_type=capability.license_type,
        )

    def _resolve_complexity_record(self, capability_id: str, version: str) -> ComplexityMultiplierRecord | None:
        records = self._state["references"].get("complexity_multipliers", [])
        now = _utc_now()
        matching: List[ComplexityMultiplierRecord] = []
        for row in records:
            if str(row.get("capability_id", "")) != capability_id:
                continue
            if str(row.get("version", "")) != version:
                continue
            try:
                rec = ComplexityMultiplierRecord(**row)
            except Exception:
                continue
            if rec.approval_state != "approved":
                continue
            start = _to_datetime(rec.effective_from)
            end = _to_datetime(rec.effective_to) if rec.effective_to else None
            if now < start:
                continue
            if end and now > end:
                continue
            matching.append(rec)

        if not matching:
            return None

        return sorted(matching, key=lambda x: x.effective_from)[-1]

    def calculate_run_cost(self, capability_id: str, version: str, input_payload: Dict[str, Any]) -> RunCostBreakdown:
        pricing = self._state["references"].get("provider_pricing", {})
        models = pricing.get("models", {}) if isinstance(pricing, dict) else {}
        default_model = str(pricing.get("default_model", "default")) if isinstance(pricing, dict) else "default"

        token_usage = input_payload.get("token_usage", {})
        prompt_tokens = float(token_usage.get("prompt_tokens", 0) or 0)
        completion_tokens = float(token_usage.get("completion_tokens", 0) or 0)
        model_name = str(token_usage.get("model", default_model))

        model_rates = models.get(model_name) or models.get(default_model) or {"input_per_1k": 0.0, "output_per_1k": 0.0}
        input_per_1k = float(model_rates.get("input_per_1k", 0.0) or 0.0)
        output_per_1k = float(model_rates.get("output_per_1k", 0.0) or 0.0)

        token_cost = (prompt_tokens / 1000.0 * input_per_1k) + (completion_tokens / 1000.0 * output_per_1k)

        tool_cost = 0.0
        estimated = False
        if isinstance(input_payload.get("tool_costs"), list) and input_payload.get("tool_costs"):
            for row in input_payload["tool_costs"]:
                if isinstance(row, dict):
                    tool_cost += float(row.get("cost_usd", 0.0) or 0.0)
        else:
            tool_usage = input_payload.get("tool_usage", [])
            tool_rates = pricing.get("tool_pricing", {}) if isinstance(pricing, dict) else {}
            if isinstance(tool_usage, list) and tool_usage:
                for usage in tool_usage:
                    if not isinstance(usage, dict):
                        continue
                    provider = str(usage.get("provider", ""))
                    calls = float(usage.get("calls", 1) or 1)
                    rate = float(((tool_rates.get(provider) or {}).get("cost_per_call", 0.0)) or 0.0)
                    tool_cost += calls * rate
                estimated = True

        complexity_record = self._resolve_complexity_record(capability_id, version)
        multiplier = complexity_record.multiplier if complexity_record else 1.0

        total_cost = token_cost * multiplier + tool_cost

        return RunCostBreakdown(
            token_cost=round(token_cost, 6),
            complexity_multiplier=round(multiplier, 6),
            base_cost_before_multiplier=round(token_cost, 6),
            external_tool_cost=round(tool_cost, 6),
            external_tool_estimated=estimated,
            total_cost=round(total_cost, 6),
            pricing_source="provider_pricing_table",
        )

    def write_financial_ledger(self, run: RunRecord, cost: RunCostBreakdown) -> FinancialLedgerEntry:
        if run.billing_track is None:
            raise StoreError("Run is missing billing_track")

        entry = FinancialLedgerEntry(
            entry_id=f"fin-{uuid.uuid4().hex[:12]}",
            created_at=_now_iso(),
            tenant_id=run.tenant_id,
            run_id=run.run_id,
            principal_id=run.principal_id,
            capability_id=run.capability_id,
            capability_version=run.version,
            amount_usd=cost.total_cost,
            token_cost_usd=cost.token_cost,
            tool_cost_usd=cost.external_tool_cost,
            complexity_multiplier=cost.complexity_multiplier,
            estimated=cost.external_tool_estimated,
            track=run.billing_track,
            venture_id=run.venture_id,
            client_id=run.client_id,
            purge_due_at=(_utc_now() + timedelta(days=365 * 7)).isoformat(),
        )
        self._state["financial_ledger"].append(entry.model_dump(mode="json"))
        self._persist()
        return entry

    def set_pending_execution(
        self,
        run_id: str,
        *,
        pending_polls: int,
        receipt_id: str,
        step_scope: str,
        manifest_ref: str,
        token_jti: str,
    ) -> None:
        row = self._state["runs"].get(run_id)
        if row is None:
            raise StoreError(f"Run not found: {run_id}")
        row["_pending_execution"] = {
            "pending_polls": max(0, pending_polls),
            "receipt_id": receipt_id,
            "step_scope": step_scope,
            "manifest_ref": manifest_ref,
            "token_jti": token_jti,
        }
        self._persist()

    def tick_pending_execution(self, run_id: str) -> Dict[str, Any] | None:
        row = self._state["runs"].get(run_id)
        if row is None:
            raise StoreError(f"Run not found: {run_id}")

        pending = row.get("_pending_execution")
        if not pending:
            return None

        remaining = int(pending.get("pending_polls", 0))
        if remaining > 0:
            pending["pending_polls"] = remaining - 1
            self._persist()
            return {"ready": False, "pending_polls": pending["pending_polls"]}

        row.pop("_pending_execution", None)
        self._persist()
        return {"ready": True, **pending}

    def retention_sweep(self, now: datetime | None = None) -> RetentionSweepResult:
        current = now or _utc_now()
        purged_disclosures = 0
        purged_diagnostics = 0
        purged_receipts = 0
        purged_audit_logs = 0
        purged_financial = 0

        disclosures = self._state["disclosures"]
        for disclosure_id in list(disclosures.keys()):
            purge_due_at = disclosures[disclosure_id].get("purge_due_at")
            if purge_due_at and _to_datetime(purge_due_at) <= current:
                del disclosures[disclosure_id]
                purged_disclosures += 1

        runs = self._state["runs"]
        for run in runs.values():
            expire_at = run.get("_diagnostics_expire_at")
            if expire_at and _to_datetime(expire_at) <= current:
                run.pop("diagnostics_redacted", None)
                run.pop("_diagnostics_expire_at", None)
                purged_diagnostics += 1

        receipts = self._state["receipts"]
        for receipt_id in list(receipts.keys()):
            purge_due_at = receipts[receipt_id].get("purge_due_at")
            if purge_due_at and _to_datetime(purge_due_at) <= current:
                del receipts[receipt_id]
                purged_receipts += 1

        audit_logs = self._state["audit_logs"]
        retained_audit: List[Dict[str, Any]] = []
        for row in audit_logs:
            purge_due_at = row.get("purge_due_at")
            if purge_due_at and _to_datetime(purge_due_at) <= current:
                purged_audit_logs += 1
            else:
                retained_audit.append(row)
        self._state["audit_logs"] = retained_audit

        retained_financial: List[Dict[str, Any]] = []
        for row in self._state["financial_ledger"]:
            purge_due_at = row.get("purge_due_at")
            if purge_due_at and _to_datetime(purge_due_at) <= current:
                purged_financial += 1
            else:
                retained_financial.append(row)
        self._state["financial_ledger"] = retained_financial

        idempotency = self._state["idempotency"]
        for dedupe_scope in list(idempotency.keys()):
            expire_at = idempotency[dedupe_scope].get("expires_at")
            if expire_at and _to_datetime(expire_at) <= current:
                del idempotency[dedupe_scope]

        confirmation_id = f"purge-{uuid.uuid4().hex[:12]}"
        confirmation = {
            "confirmation_id": confirmation_id,
            "created_at": current.isoformat(),
            "purged_disclosures": purged_disclosures,
            "purged_diagnostics": purged_diagnostics,
            "purged_receipts": purged_receipts,
            "purged_audit_logs": purged_audit_logs,
            "purged_financial_ledger": purged_financial,
            "immutable_hash": _hash_text(
                json.dumps(
                    {
                        "at": current.isoformat(),
                        "disclosures": purged_disclosures,
                        "diagnostics": purged_diagnostics,
                        "receipts": purged_receipts,
                        "audit": purged_audit_logs,
                        "financial": purged_financial,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            ),
        }
        self._state["purge_confirmations"].append(confirmation)

        self._persist()
        return RetentionSweepResult(
            swept_at=current.isoformat(),
            purged_disclosures=purged_disclosures,
            purged_diagnostics=purged_diagnostics,
            purged_receipts=purged_receipts,
            purged_audit_logs=purged_audit_logs,
            purged_financial_ledger=purged_financial,
            confirmation_id=confirmation_id,
        )

    def _sum_spend(self, since: datetime) -> float:
        total = 0.0
        for row in self._state["financial_ledger"]:
            created_at = row.get("created_at")
            if not created_at:
                continue
            if _to_datetime(str(created_at)) >= since:
                total += float(row.get("amount_usd", 0.0) or 0.0)
        return total

    def _dominant_tenant_since(self, since: datetime) -> str | None:
        totals: Dict[str, float] = {}
        for row in self._state["financial_ledger"]:
            created_at = row.get("created_at")
            if not created_at:
                continue
            if _to_datetime(str(created_at)) < since:
                continue
            tenant_id = str(row.get("tenant_id", "")).strip()
            if not tenant_id:
                continue
            totals[tenant_id] = totals.get(tenant_id, 0.0) + float(row.get("amount_usd", 0.0) or 0.0)
        if not totals:
            return None
        return sorted(totals.items(), key=lambda item: item[1], reverse=True)[0][0]

    def _monthly_projection(self, now: datetime) -> float:
        start, end = _month_bounds(now)
        elapsed = (now - start).total_seconds()
        total_window = (end - start).total_seconds()
        if elapsed <= 0:
            return 0.0

        month_spend = self._sum_spend(start)
        return month_spend / elapsed * total_window

    def evaluate_level2_triggers(self) -> List[str]:
        now = _utc_now()
        triggered: List[str] = []
        runaway_triggered = False
        security_triggered = False
        candidate_scope_tenants: set[str] = set()

        spend_15m = self._sum_spend(now - timedelta(minutes=15))
        if spend_15m > 75.0:
            triggered.append("runaway_cost_15m_over_75")
            runaway_triggered = True

        spend_10m = self._sum_spend(now - timedelta(minutes=10))
        spend_24h = self._sum_spend(now - timedelta(hours=24))
        if spend_24h > 0:
            baseline_10m = spend_24h / (24.0 * 6.0)
            if baseline_10m > 0 and spend_10m > (3.0 * baseline_10m):
                triggered.append("runaway_cost_burn_rate_3x_10m")
                runaway_triggered = True

        projected_month_end = self._monthly_projection(now)
        protection_state = self._state["protection_state"]
        bucket = _five_minute_bucket(now)
        if bucket != protection_state.get("last_projected_bucket"):
            if projected_month_end > 1000.0:
                protection_state["projected_over_cap_streak"] = int(protection_state.get("projected_over_cap_streak", 0)) + 1
            else:
                protection_state["projected_over_cap_streak"] = 0
            protection_state["last_projected_bucket"] = bucket

        if int(protection_state.get("projected_over_cap_streak", 0)) >= 2:
            triggered.append("runaway_cost_projected_month_over_1000")
            runaway_triggered = True

        if runaway_triggered:
            dominant_tenant = self._dominant_tenant_since(now - timedelta(minutes=15))
            if dominant_tenant:
                candidate_scope_tenants.add(dominant_tenant)

        security_events = self._state["security_events"]
        critical_last_10m = 0
        source_failures_5m: Dict[str, int] = {}
        source_tenants_5m: Dict[str, set[str]] = {}
        credential_compromise = False

        for row in security_events:
            created_raw = row.get("created_at")
            if not created_raw:
                continue
            created_at = _to_datetime(str(created_raw))
            if created_at >= now - timedelta(minutes=10) and str(row.get("severity", "")) == "critical":
                critical_last_10m += 1
                tenant_id = str(row.get("tenant_id", "")).strip()
                if tenant_id:
                    candidate_scope_tenants.add(tenant_id)

            if created_at >= now - timedelta(minutes=5):
                event_type = str(row.get("event_type", ""))
                if event_type == "invalid_signature_replay":
                    source = str(row.get("source", "unknown"))
                    source_failures_5m[source] = source_failures_5m.get(source, 0) + 1
                    source_tenants = source_tenants_5m.setdefault(source, set())
                    tenant_id = str(row.get("tenant_id", "")).strip()
                    if tenant_id:
                        source_tenants.add(tenant_id)

            if str(row.get("event_type", "")) == "credential_compromise_confirmed":
                credential_compromise = True
                tenant_id = str(row.get("tenant_id", "")).strip()
                if tenant_id:
                    candidate_scope_tenants.add(tenant_id)

        if critical_last_10m >= 3:
            triggered.append("security_critical_exceptions_10m")
            security_triggered = True

        if any(count >= 10 for count in source_failures_5m.values()):
            triggered.append("security_invalid_signature_spike")
            security_triggered = True
            noisy_sources = [source for source, count in source_failures_5m.items() if count >= 10]
            for source in noisy_sources:
                candidate_scope_tenants.update(source_tenants_5m.get(source, set()))

        if credential_compromise:
            triggered.append("security_credential_compromise")
            security_triggered = True

        if triggered:
            # Scoped by default; global only when scope cannot be isolated confidently
            # or when both risk classes trigger simultaneously.
            if len(candidate_scope_tenants) == 1 and not (runaway_triggered and security_triggered):
                scope_type = KillSwitchScopeType.TENANT
                scope_id = list(candidate_scope_tenants)[0]
            else:
                scope_type = KillSwitchScopeType.PLATFORM
                scope_id = "global"

            hard_cancel = any(key.startswith("runaway_cost") or key.startswith("security_") for key in triggered)
            self.set_kill_switch(
                level=KillSwitchLevel.LEVEL_2,
                scope_type=scope_type,
                scope_id=scope_id,
                reason=",".join(triggered),
                hard_cancel_inflight=hard_cancel,
                activated_by="auto-threshold-guard",
            )
            for key in triggered:
                self.add_alert(f"Level-2 automated trigger fired: {key}")

        return triggered

    def record_evaluation(
        self,
        *,
        run_id: str,
        capability_id: str,
        version: str,
        confidence: float,
        critical_failure: bool,
    ) -> List[str]:
        events = self._state["evaluation_history"]
        events.append(
            {
                "run_id": run_id,
                "capability_id": capability_id,
                "version": version,
                "confidence": confidence,
                "critical_failure": critical_failure,
                "created_at": _now_iso(),
            }
        )
        self._state["evaluation_history"] = events[-1000:]

        triggered: List[str] = []
        scoped = [row for row in self._state["evaluation_history"] if row.get("capability_id") == capability_id]
        rolling = scoped[-100:]
        if len(rolling) >= 30:
            avg_confidence = sum(float(row.get("confidence", 0.0) or 0.0) for row in rolling) / len(rolling)
            if avg_confidence < 0.80:
                triggered.append("level3_confidence_below_0_80")

        critical_streak = 0
        for row in reversed(scoped):
            if bool(row.get("critical_failure", False)):
                critical_streak += 1
            else:
                break
        if critical_streak >= 3:
            triggered.append("level3_severe_consecutive_critical_failure")

        if triggered:
            rollback_version = self._last_certified_version_before(capability_id, version)
            self._state["rollback_actions"].append(
                {
                    "action_id": f"rb-{uuid.uuid4().hex[:12]}",
                    "created_at": _now_iso(),
                    "capability_id": capability_id,
                    "from_version": version,
                    "to_version": rollback_version,
                    "reasons": triggered,
                }
            )
            self.set_kill_switch(
                level=KillSwitchLevel.LEVEL_3,
                scope_type=KillSwitchScopeType.WORKLOAD,
                scope_id=capability_id,
                reason=",".join(triggered),
                hard_cancel_inflight=True,
                activated_by="auto-deterministic-reversion",
            )
            for reason in triggered:
                self.add_alert(f"Level-3 trigger fired: {reason}")

        self._persist()
        return triggered

    def _last_certified_version_before(self, capability_id: str, current_version: str) -> str:
        candidates = [item for item in self.list_capabilities() if item.capability_id == capability_id]
        sorted_candidates = sorted(candidates, key=lambda x: _semantic_key(x.version))
        current_key = _semantic_key(current_version)
        fallback = current_version
        for capability in sorted_candidates:
            if _semantic_key(capability.version) >= current_key:
                break
            policy = self.get_capability_policy(capability.capability_id, capability.version)
            if policy.certification_state.value == "certified":
                fallback = capability.version
        return fallback

    def get_receipt_for_run(self, run_id: str) -> Optional[ExecutionReceipt]:
        for row in self._state["receipts"].values():
            if str(row.get("run_id", "")) == run_id:
                return ExecutionReceipt(**row)
        return None

    def measure_slo(self) -> OpsSLOSummary:
        usage = self._state.get("usage_events", [])
        if not usage:
            return OpsSLOSummary(
                uptime_target_percent=self.settings.class_a_uptime_target,
                p95_target_seconds=self.settings.class_a_p95_target_seconds,
                measured_uptime_percent=100.0,
                measured_p95_seconds=0.0,
                within_target=True,
            )

        total = len(usage)
        success = len([row for row in usage if bool(row.get("success", False))])
        uptime = (success / total) * 100.0 if total else 100.0

        latencies = sorted(int(row.get("latency_ms", 0) or 0) for row in usage)
        index = max(0, int(math.ceil(0.95 * len(latencies))) - 1)
        p95_seconds = latencies[index] / 1000.0

        within = uptime >= self.settings.class_a_uptime_target and p95_seconds <= self.settings.class_a_p95_target_seconds
        return OpsSLOSummary(
            uptime_target_percent=self.settings.class_a_uptime_target,
            p95_target_seconds=self.settings.class_a_p95_target_seconds,
            measured_uptime_percent=round(uptime, 3),
            measured_p95_seconds=round(p95_seconds, 3),
            within_target=within,
        )

    def dashboard(self) -> OpsDashboard:
        now = _utc_now()
        slo = self.measure_slo()
        alerts = self.get_active_alerts()
        if not slo.within_target:
            alerts = [*alerts, "SLO breach: uptime/p95 outside Class A target"]
        return OpsDashboard(
            generated_at=now.isoformat(),
            kill_switch=self.get_kill_switch(),
            slo=slo,
            spend_last_15m_usd=round(self._sum_spend(now - timedelta(minutes=15)), 6),
            spend_last_24h_usd=round(self._sum_spend(now - timedelta(hours=24)), 6),
            projected_month_end_usd=round(self._monthly_projection(now), 6),
            active_alerts=alerts,
        )
