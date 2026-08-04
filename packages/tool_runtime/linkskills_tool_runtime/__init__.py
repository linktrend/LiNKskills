"""LiNKskills tool runtime — descriptor load, exact resolve, local invoke."""

from .descriptor import ToolDescriptor, hash_tool_source_tree, load_tool_descriptor
from .invoke import ToolInvocationResult, invoke_tool
from .resolve import ResolvedTool, ResolutionError, resolve_tool

__all__ = [
    "ResolutionError",
    "ResolvedTool",
    "ToolDescriptor",
    "ToolInvocationResult",
    "hash_tool_source_tree",
    "invoke_tool",
    "load_tool_descriptor",
    "resolve_tool",
]

__version__ = "0.1.0"
