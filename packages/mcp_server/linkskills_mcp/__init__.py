"""LiNKskills MCP adapter — JSON-RPC tools over SkillsGatewayService."""

from .paci_stdio_proxy import PaciStdioMcpProxy, build_paci_client
from .server import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION, SkillsMcpServer, main

__all__ = [
    "PROTOCOL_VERSION",
    "SERVER_NAME",
    "SERVER_VERSION",
    "SkillsMcpServer",
    "PaciStdioMcpProxy",
    "build_paci_client",
    "main",
]

__version__ = "0.1.0"
