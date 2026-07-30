"""LiNKskills Gateway — stdlib HTTP JSON API over domain operations."""

from .auth import (
    ActorClaims,
    AuthConfigurationError,
    AuthError,
    LocalUnsignedClaimsVerifier,
    PlatformClaimsVerifier,
    resolve_claims_verifier,
)
from .ops import (
    DrainState,
    GatewayMetrics,
    ShutdownResult,
    auth_config_present,
    run_graceful_shutdown,
)
from .service import SkillsGatewayService, OPERATIONS
from .server import create_server, make_handler, serve_until_shutdown

__all__ = [
    "ActorClaims",
    "AuthConfigurationError",
    "AuthError",
    "DrainState",
    "GatewayMetrics",
    "LocalUnsignedClaimsVerifier",
    "PlatformClaimsVerifier",
    "ShutdownResult",
    "auth_config_present",
    "resolve_claims_verifier",
    "run_graceful_shutdown",
    "serve_until_shutdown",
    "SkillsGatewayService",
    "OPERATIONS",
    "create_server",
    "make_handler",
]

__version__ = "0.1.0"
