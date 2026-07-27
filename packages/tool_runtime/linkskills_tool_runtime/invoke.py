"""Resolve + invoke packaged tools with a structured result."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

from .adapters import AdapterResult, LocalProcessAdapter, ServerAdapter
from .resolve import ResolvedTool, resolve_tool


@dataclass
class ToolInvocationResult:
    """Structured result of resolve + invoke."""

    ok: bool
    tool_id: str
    version: str
    bundle_hash: Optional[str]
    exit_code: Optional[int]
    stdout: str
    stderr: str
    adapter_kind: str
    timed_out: bool = False
    error: Optional[str] = None
    resolved: Optional[ResolvedTool] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "tool_id": self.tool_id,
            "version": self.version,
            "bundle_hash": self.bundle_hash,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "adapter_kind": self.adapter_kind,
            "timed_out": self.timed_out,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


def invoke_tool(
    tool_dir: Union[str, Path],
    *,
    tool_id: Optional[str] = None,
    version: Optional[str] = None,
    bundle_hash: Optional[str] = None,
    source_hash: Optional[str] = None,
    argv: Optional[Sequence[str]] = None,
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout_seconds: Optional[float] = None,
    input_text: Optional[str] = None,
    adapter: str = "local",
) -> ToolInvocationResult:
    """Resolve a tool exactly, then invoke via the selected adapter."""
    resolved = resolve_tool(
        tool_dir,
        tool_id=tool_id,
        version=version,
        bundle_hash=bundle_hash,
        source_hash=source_hash,
    )

    if adapter in {"local", "local_process"}:
        runner = LocalProcessAdapter()
        result: AdapterResult = runner.invoke(
            resolved,
            argv=argv,
            cwd=cwd,
            env=env,
            timeout_seconds=timeout_seconds,
            input_text=input_text,
        )
        adapter_kind = runner.kind
    elif adapter in {"server", "remote"}:
        runner_server = ServerAdapter()
        try:
            result = runner_server.invoke(
                resolved,
                argv=argv,
                cwd=cwd,
                env=env,
                timeout_seconds=timeout_seconds,
                input_text=input_text,
            )
        except NotImplementedError as exc:
            return ToolInvocationResult(
                ok=False,
                tool_id=resolved.tool_id,
                version=resolved.version,
                bundle_hash=resolved.bundle_hash,
                exit_code=None,
                stdout="",
                stderr="",
                adapter_kind=runner_server.kind,
                error=str(exc),
                resolved=resolved,
            )
        adapter_kind = runner_server.kind
    else:
        return ToolInvocationResult(
            ok=False,
            tool_id=resolved.tool_id,
            version=resolved.version,
            bundle_hash=resolved.bundle_hash,
            exit_code=None,
            stdout="",
            stderr="",
            adapter_kind=adapter,
            error=f"unknown adapter: {adapter!r}",
            resolved=resolved,
        )

    return ToolInvocationResult(
        ok=result.ok,
        tool_id=resolved.tool_id,
        version=resolved.version,
        bundle_hash=resolved.bundle_hash,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
        adapter_kind=adapter_kind,
        timed_out=result.timed_out,
        error=result.error,
        resolved=resolved,
        metadata=dict(result.metadata),
    )
