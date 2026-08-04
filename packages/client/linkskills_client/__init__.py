"""LiNKskills generic HTTP client and skill_runtime compatibility wrappers."""

from .client import BufferedEvent, LocalEventBuffer, SkillsGatewayClient
from .compat import load_skill, record_invocation
from .paci_token_client import (
    PaciAuthError,
    PaciClientConfig,
    PaciConfigError,
    PaciTokenClient,
    PaciTokenError,
    PaciTransientError,
    MAX_ACCESS_TTL_S,
    paci_env_configured,
    refuse_brain_openclaw_reuse,
    require_https_outside_local_test,
)

__all__ = [
    "BufferedEvent",
    "LocalEventBuffer",
    "MAX_ACCESS_TTL_S",
    "PaciAuthError",
    "PaciClientConfig",
    "PaciConfigError",
    "PaciTokenClient",
    "PaciTokenError",
    "PaciTransientError",
    "SkillsGatewayClient",
    "load_skill",
    "paci_env_configured",
    "record_invocation",
    "refuse_brain_openclaw_reuse",
    "require_https_outside_local_test",
]


__version__ = "0.1.0"
