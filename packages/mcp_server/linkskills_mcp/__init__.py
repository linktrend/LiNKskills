"""LiNKskills MCP adapter — JSON-RPC tools over SkillsGatewayService."""

from .paci_stdio_proxy import PaciStdioMcpProxy, build_paci_client
from .server import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION, SkillsMcpServer, main
from .v2_provider import ModernSkillsMcpServer, V2Provider

__all__ = [
    "PROTOCOL_VERSION",
    "SERVER_NAME",
    "SERVER_VERSION",
    "SkillsMcpServer",
    "ModernSkillsMcpServer",
    "V2Provider",
    "PaciStdioMcpProxy",
    "build_paci_client",
    "main",
]

__version__ = "0.1.0"
