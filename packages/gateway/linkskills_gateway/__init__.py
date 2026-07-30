"""LiNKskills Gateway — stdlib HTTP JSON API over domain operations."""

from .auth import (
    ActorClaims,
    AuthConfigurationError,
    AuthError,
    LocalUnsignedClaimsVerifier,
    PlatformClaimsVerifier,
    resolve_claims_verifier,
)
from .ops import DrainState, GatewayMetrics, auth_config_present
from .service import SkillsGatewayService, OPERATIONS
from .server import create_server, make_handler

__all__ = [
    "ActorClaims",
    "AuthConfigurationError",
    "AuthError",
    "DrainState",
    "GatewayMetrics",
    "LocalUnsignedClaimsVerifier",
    "PlatformClaimsVerifier",
    "auth_config_present",
    "resolve_claims_verifier",
    "SkillsGatewayService",
    "OPERATIONS",
    "create_server",
    "make_handler",
]

__version__ = "0.1.0"
