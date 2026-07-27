"""LiNKskills MCP adapter — JSON-RPC tools over SkillsGatewayService."""

from .server import PROTOCOL_VERSION, SERVER_NAME, SERVER_VERSION, SkillsMcpServer, main

__all__ = [
    "PROTOCOL_VERSION",
    "SERVER_NAME",
    "SERVER_VERSION",
    "SkillsMcpServer",
    "main",
]

__version__ = "0.1.0"
