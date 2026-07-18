from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class CapabilitySourceType(str, Enum):
    SKILL = "skill"
    TOOL = "tool"


class CapabilityClass(str, Enum):
    CLASS_A = "class_a"
    CLASS_B = "class_b"
    CLASS_C = "class_c"


class LicenseType(str, Enum):
    STANDARD = "standard"
    STUDIO_PROPRIETARY = "studio_proprietary"


class CertificationState(str, Enum):
    CERTIFIED = "certified"
    CANDIDATE = "candidate"
    REVOKED = "revoked"


class ActivationState(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class LifecycleState(str, Enum):
    DRAFT = "draft"
    INTERNAL = "internal"
    BETA = "beta"
    PUBLIC = "public"
    DEPRECATED = "deprecated"


class VisibilityClass(str, Enum):
    INTERNAL = "internal"
    PRIVATE = "private"
    PUBLIC = "public"


class ExecutionMode(str, Enum):
    MANAGED = "MANAGED"


class RequestOrigin(str, Enum):
    INTERNAL = "INTERNAL"
    AIOS = "AIOS"


class BillingTrack(str, Enum):
    TRACK_1 = "track_1"
    TRACK_2 = "track_2"


class RunStatus(str, Enum):
    INITIALIZED = "initialized"
    AWAITING_DISCLOSURE = "awaiting_disclosure"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    EVALUATION_FAILED = "evaluation_failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PURGED = "purged"
    POLICY_DENIED = "policy_denied"


class KillSwitchLevel(str, Enum):
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"


class KillSwitchScopeType(str, Enum):
    PLATFORM = "platform"
    TENANT = "tenant"
    WORKLOAD = "workload"


class ApiKeyState(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class RetentionClass(str, Enum):
    SUCCESS_METADATA_ONLY = "success_metadata_only"
    FAILURE_REDACTED_30D = "failure_redacted_30d"
    DISCLOSURE_AUDIT_180D = "disclosure_audit_180d"
    FINANCIAL_LEDGER_7Y = "financial_ledger_7y"


class SourceTrace(BaseModel):
    repo_commit_sha: str
    source_path_hash: str
    extracted_at: str
    extractor_version: str
    source_paths: List[str]


class CapabilityContract(BaseModel):
    capability_id: str
    source_type: CapabilitySourceType
    version: str
    name: str
    description: str
    lifecycle_state: LifecycleState
    visibility: VisibilityClass
    execution_modes: List[ExecutionMode]
    disclosure_mode: str
    input_schema_ref: Optional[str] = None
    output_schema_ref: Optional[str] = None
    source_trace: SourceTrace
    capability_class: CapabilityClass = CapabilityClass.CLASS_A
    license_type: LicenseType = LicenseType.STANDARD
    certification_state: CertificationState = CertificationState.CERTIFIED
    activation_state: ActivationState = ActivationState.ACTIVE
    active_from: Optional[str] = None


class PackageContract(BaseModel):
    package_id: str
    version: str
    included_capabilities: List[str]
    step_order: List[str]
    gates: List[str]
    policy_profile: str
    lifecycle_state: LifecycleState = LifecycleState.INTERNAL
    visibility: VisibilityClass = VisibilityClass.INTERNAL


class ApiKeyRecord(BaseModel):
    key_id: str
    key_hash: str
    tenant_id: str
    principal_id: str
    state: ApiKeyState
    created_at: str
    rotated_at: Optional[str] = None
    revoked_at: Optional[str] = None
    last_used_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DprRegistryRecord(BaseModel):
    dpr_id: str
    active: bool
    tenant_id: Optional[str] = None
    notes: Optional[str] = None


class CapabilityVersionPolicy(BaseModel):
    capability_id: str
    version: str
    certification_state: CertificationState = CertificationState.CERTIFIED
    activation_state: ActivationState = ActivationState.ACTIVE
    capability_class: CapabilityClass = CapabilityClass.CLASS_A
    visibility: VisibilityClass = VisibilityClass.INTERNAL
    license_type: LicenseType = LicenseType.STANDARD
    allowed_tenants: List[str] = Field(default_factory=list)
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


class ComplexityMultiplierRecord(BaseModel):
    capability_id: str
    version: str
    multiplier: float
    effective_from: str
    effective_to: Optional[str] = None
    proposed_by: str
    approved_by: Optional[str] = None
    approval_state: Literal["proposed", "approved", "rejected"] = "proposed"


class OverrideApprovalRecord(BaseModel):
    override_id: str
    capability_id: str
    tenant_id: str
    authority_chain: List[str]
    approved: bool
    emergency: bool
    created_at: str


class RunCostBreakdown(BaseModel):
    token_cost: float = 0.0
    complexity_multiplier: float = 1.0
    base_cost_before_multiplier: float = 0.0
    external_tool_cost: float = 0.0
    external_tool_estimated: bool = False
    total_cost: float = 0.0
    currency: str = "USD"
    pricing_source: str = "provider_pricing_table"


class RunCreateRequest(BaseModel):
    tenant_id: str
    principal_id: str
    idempotency_key: str
    capability_id: Optional[str] = None
    package_id: Optional[str] = None
    version: Optional[str] = None
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    context_refs: List[str] = Field(default_factory=list)
    mode: ExecutionMode = ExecutionMode.MANAGED
    origin: RequestOrigin = RequestOrigin.INTERNAL
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    dpr_id: Optional[str] = None
    billing_track: BillingTrack
    venture_id: Optional[str] = None
    client_id: Optional[str] = None

    @model_validator(mode="after")
    def _validate_target(self) -> "RunCreateRequest":
        has_capability = bool(self.capability_id)
        has_package = bool(self.package_id)
        if has_capability == has_package:
            raise ValueError("Exactly one of capability_id or package_id must be supplied")
        return self

    @model_validator(mode="after")
    def _validate_aios_identity(self) -> "RunCreateRequest":
        if self.origin == RequestOrigin.AIOS:
            missing: List[str] = []
            if not self.mission_id:
                missing.append("mission_id")
            if not self.task_id:
                missing.append("task_id")
            if not self.dpr_id:
                missing.append("dpr_id")
            if missing:
                raise ValueError(f"AIOS origin requires fields: {', '.join(missing)}")
        return self

    @model_validator(mode="after")
    def _validate_billing_identity(self) -> "RunCreateRequest":
        if self.venture_id and self.client_id:
            raise ValueError("Billing identity must include exactly one of venture_id or client_id")

        if self.billing_track == BillingTrack.TRACK_1:
            if not self.venture_id or self.client_id:
                raise ValueError("Track 1 requires venture_id and forbids client_id")
        elif self.billing_track == BillingTrack.TRACK_2:
            if not self.client_id or self.venture_id:
                raise ValueError("Track 2 requires client_id and forbids venture_id")

        return self


class RunCreateResponse(BaseModel):
    run_id: str
    status: RunStatus
    disclosure_required: bool
    next_action: str
    idempotent_replay: bool = False


class RunRecord(BaseModel):
    run_id: str
    tenant_id: str
    principal_id: str
    capability_id: str
    version: str
    status: RunStatus
    started_at: str
    completed_at: Optional[str] = None
    error_class: Optional[str] = None
    output_metadata: Dict[str, Any] = Field(default_factory=dict)
    diagnostics_redacted: Optional[Dict[str, Any]] = None
    context_refs: List[str] = Field(default_factory=list)
    policy_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    dpr_id: Optional[str] = None
    billing_track: Optional[BillingTrack] = None
    venture_id: Optional[str] = None
    client_id: Optional[str] = None
    cost_breakdown: Optional[RunCostBreakdown] = None


class DisclosureIssueRequest(BaseModel):
    run_id: str
    step_scope: str
    idempotency_key: str


class DisclosureIssueResponse(BaseModel):
    disclosure_token: str
    expires_at: str
    manifest_ref: str
    run_status: RunStatus
    receipt_id: str
    terminal: bool
    idempotent_replay: bool = False


class DisclosureTokenClaims(BaseModel):
    tenant_id: str
    run_id: str
    capability_id: str
    version: str
    step_scope: str
    mode: Literal["MANAGED"]
    exp: int
    jti: str


class ExecutionReceipt(BaseModel):
    receipt_id: str
    run_id: str
    result_status: RunStatus
    policy_summary: List[Dict[str, Any]]
    retention_class: RetentionClass
    evidence_hashes: List[str]
    data_purge_status: str
    created_at: str
    purge_due_at: Optional[str] = None
    cost_breakdown: Optional[RunCostBreakdown] = None
    audit_refs: List[str] = Field(default_factory=list)


class IdempotencyRecord(BaseModel):
    dedupe_scope: str
    endpoint: str
    tenant_id: str
    principal_id: str
    idempotency_key: str
    payload_hash: str
    response_payload: Dict[str, Any]
    status_code: int
    created_at: str
    expires_at: str


class KillSwitchState(BaseModel):
    level: KillSwitchLevel = KillSwitchLevel.LEVEL_1
    scope_type: KillSwitchScopeType = KillSwitchScopeType.PLATFORM
    scope_id: str = "global"
    reason: str = "normal_operations"
    hard_cancel_inflight: bool = False
    activated_at: Optional[str] = None
    activated_by: Optional[str] = None


class UsageEvent(BaseModel):
    event_id: str
    created_at: str
    tenant_id: str
    principal_id: str
    action: str
    endpoint: str
    run_id: Optional[str] = None
    latency_ms: int
    success: bool
    dimensions: Dict[str, Any] = Field(default_factory=dict)


class SecurityEvent(BaseModel):
    event_id: str
    created_at: str
    source: str
    tenant_id: Optional[str] = None
    principal_id: Optional[str] = None
    event_type: str
    severity: Literal["info", "warning", "critical"] = "info"
    details: Dict[str, Any] = Field(default_factory=dict)


class FinancialLedgerEntry(BaseModel):
    entry_id: str
    created_at: str
    tenant_id: str
    run_id: str
    principal_id: str
    capability_id: str
    capability_version: str
    amount_usd: float
    token_cost_usd: float
    tool_cost_usd: float
    complexity_multiplier: float
    estimated: bool
    track: BillingTrack
    venture_id: Optional[str] = None
    client_id: Optional[str] = None
    purge_due_at: str


class CatalogSnapshot(BaseModel):
    generated_at: str
    repo_root: str
    manifest_entries: int
    capabilities: List[CapabilityContract]
    packages: List[PackageContract]
    extraction_warnings: List[str] = Field(default_factory=list)


class AuditEvent(BaseModel):
    event_id: str
    created_at: str
    tenant_id: str
    principal_id: str
    action: str
    target_id: str
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)


class RetentionSweepResult(BaseModel):
    swept_at: str
    purged_disclosures: int
    purged_diagnostics: int
    purged_receipts: int
    purged_audit_logs: int
    purged_financial_ledger: int
    confirmation_id: str


class OpsSLOSummary(BaseModel):
    uptime_target_percent: float
    p95_target_seconds: float
    measured_uptime_percent: float
    measured_p95_seconds: float
    within_target: bool


class OpsDashboard(BaseModel):
    generated_at: str
    kill_switch: KillSwitchState
    slo: OpsSLOSummary
    spend_last_15m_usd: float
    spend_last_24h_usd: float
    projected_month_end_usd: float
    active_alerts: List[str]
