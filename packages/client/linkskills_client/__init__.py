"""LiNKskills generic HTTP client and skill_runtime compatibility wrappers."""

from .client import BufferedEvent, LocalEventBuffer, SkillsGatewayClient
from .compat import load_skill, record_invocation

__all__ = [
    "BufferedEvent",
    "LocalEventBuffer",
    "SkillsGatewayClient",
    "load_skill",
    "record_invocation",
]

__version__ = "0.1.0"
