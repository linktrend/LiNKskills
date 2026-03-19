from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    catalog_path: Path
    packages_path: Path
    data_path: Path
    api_keys_path: Path
    dpr_registry_path: Path
    complexity_path: Path
    provider_pricing_path: Path
    capability_policy_path: Path
    class_b_entitlements_path: Path
    override_approvals_path: Path
    environment: str
    secret_provider: str
    gcp_project_id: str | None
    gsm_secret_file: Path
    allow_nonprod_secret_fallback: bool
    token_secret_env_key: str
    token_ttl_seconds: int
    execution_timeout_seconds: int
    idempotency_ttl_hours: int
    internal_tenant_default: str
    internal_tenant_slug: str
    class_a_uptime_target: float
    class_a_p95_target_seconds: float
    bootstrap_api_key: str
    class_c_hidden_turn_enabled: bool

    @property
    def is_production(self) -> bool:
        return self.environment in {"prod", "production"}


def load_settings() -> Settings:
    repo_root = Path(os.getenv("LOGIC_ENGINE_REPO_ROOT", Path(__file__).resolve().parents[4])).resolve()
    service_root = Path(__file__).resolve().parents[2]

    catalog_path = Path(os.getenv("LOGIC_ENGINE_CATALOG_PATH", service_root / "generated" / "catalog.json")).resolve()
    packages_path = Path(os.getenv("LOGIC_ENGINE_PACKAGES_PATH", service_root / "config" / "packages.json")).resolve()
    data_path = Path(os.getenv("LOGIC_ENGINE_DATA_PATH", service_root / "runtime" / "store.json")).resolve()

    api_keys_path = Path(os.getenv("LOGIC_ENGINE_API_KEYS_PATH", service_root / "config" / "api_keys.json")).resolve()
    dpr_registry_path = Path(os.getenv("LOGIC_ENGINE_DPR_REGISTRY_PATH", service_root / "config" / "dpr_registry.json")).resolve()
    complexity_path = Path(
        os.getenv("LOGIC_ENGINE_COMPLEXITY_PATH", service_root / "config" / "complexity_multipliers.json")
    ).resolve()
    provider_pricing_path = Path(
        os.getenv("LOGIC_ENGINE_PROVIDER_PRICING_PATH", service_root / "config" / "provider_pricing.json")
    ).resolve()
    capability_policy_path = Path(
        os.getenv("LOGIC_ENGINE_CAPABILITY_POLICY_PATH", service_root / "config" / "capability_policy.json")
    ).resolve()
    class_b_entitlements_path = Path(
        os.getenv("LOGIC_ENGINE_CLASS_B_ENTITLEMENTS_PATH", service_root / "config" / "class_b_entitlements.json")
    ).resolve()
    override_approvals_path = Path(
        os.getenv("LOGIC_ENGINE_OVERRIDE_APPROVALS_PATH", service_root / "config" / "override_approvals.json")
    ).resolve()

    return Settings(
        repo_root=repo_root,
        catalog_path=catalog_path,
        packages_path=packages_path,
        data_path=data_path,
        api_keys_path=api_keys_path,
        dpr_registry_path=dpr_registry_path,
        complexity_path=complexity_path,
        provider_pricing_path=provider_pricing_path,
        capability_policy_path=capability_policy_path,
        class_b_entitlements_path=class_b_entitlements_path,
        override_approvals_path=override_approvals_path,
        environment=os.getenv("LOGIC_ENGINE_ENV", "nonprod").strip().lower(),
        secret_provider=os.getenv("LOGIC_ENGINE_SECRET_PROVIDER", "gsm").strip().lower(),
        gcp_project_id=(os.getenv("LOGIC_ENGINE_GCP_PROJECT_ID") or os.getenv("GCP_PROJECT_ID")),
        gsm_secret_file=Path(os.getenv("LOGIC_ENGINE_GSM_SECRET_FILE", service_root / "runtime" / "gsm-secrets.json")).resolve(),
        allow_nonprod_secret_fallback=_bool_env("LOGIC_ENGINE_ALLOW_NONPROD_SECRET_FALLBACK", False),
        token_secret_env_key=os.getenv("LOGIC_ENGINE_TOKEN_SECRET_ENV_KEY", "LOGIC_ENGINE_TOKEN_SECRET").strip(),
        token_ttl_seconds=int(os.getenv("LOGIC_ENGINE_TOKEN_TTL_SECONDS", "300")),
        execution_timeout_seconds=int(os.getenv("LOGIC_ENGINE_EXECUTION_TIMEOUT_SECONDS", "30")),
        idempotency_ttl_hours=int(os.getenv("LOGIC_ENGINE_IDEMPOTENCY_TTL_HOURS", "24")),
        internal_tenant_default=os.getenv(
            "LOGIC_ENGINE_INTERNAL_TENANT",
            "00000000-0000-0000-0000-000000000001",
        ).strip(),
        internal_tenant_slug=os.getenv("LOGIC_ENGINE_INTERNAL_TENANT_SLUG", "linktrend_internal").strip(),
        class_a_uptime_target=float(os.getenv("LOGIC_ENGINE_CLASS_A_UPTIME_TARGET", "99.5")),
        class_a_p95_target_seconds=float(os.getenv("LOGIC_ENGINE_CLASS_A_P95_TARGET_SECONDS", "2.0")),
        bootstrap_api_key=os.getenv("LOGIC_ENGINE_BOOTSTRAP_API_KEY", "mvo-internal-api-key").strip(),
        class_c_hidden_turn_enabled=_bool_env("LOGIC_ENGINE_CLASS_C_HIDDEN_TURN_ENABLED", False),
    )
