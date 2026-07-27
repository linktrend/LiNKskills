"""LiNKskills Gateway — stdlib HTTP JSON API over domain operations."""

from .auth import ActorClaims, AuthError, PlatformClaimsVerifier, mint_platform_token
from .service import SkillsGatewayService, OPERATIONS
from .server import create_server, make_handler

__all__ = [
    "ActorClaims",
    "AuthError",
    "PlatformClaimsVerifier",
    "mint_platform_token",
    "SkillsGatewayService",
    "OPERATIONS",
    "create_server",
    "make_handler",
]

__version__ = "0.1.0"
