"""Execution adapters for packaged tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

from .confined_exec import ConfinedExecutionError, assert_within_boundary, run_confined
from .resolve import ResolvedTool


@dataclass
class AdapterResult:
    """Structured adapter-level execution result."""

    ok: bool
    exit_code: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool = False
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class LocalProcessAdapter:
    """Run a tool as a confined local subprocess (no shell, bounded, fail-closed)."""

    kind = "local_process"

    def __init__(self, *, default_timeout_seconds: float = 30.0) -> None:
        self.default_timeout_seconds = default_timeout_seconds

    def invoke(
        self,
        resolved: ResolvedTool,
        argv: Optional[Sequence[str]] = None,
        *,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Mapping[str, str]] = None,
        timeout_seconds: Optional[float] = None,
        input_text: Optional[str] = None,
    ) -> AdapterResult:
        entry = resolved.descriptor.entrypoint or {}
        command = entry.get("command")
        if not command:
            return AdapterResult(
                ok=False,
                exit_code=None,
                stdout="",
                stderr="",
                error="descriptor entrypoint.command is missing",
            )
        if isinstance(command, str) and (" " in command.strip()):
            return AdapterResult(
                ok=False,
                exit_code=None,
                stdout="",
                stderr="",
                error=(
                    "entrypoint.command must be a single executable path; "
                    "shell strings and bash -lc are forbidden"
                ),
            )

        sandbox_root = Path(resolved.tool_dir).resolve()
        workdir_raw = cwd or entry.get("working_directory") or sandbox_root
        try:
            workdir = assert_within_boundary(workdir_raw, sandbox_root)
        except ConfinedExecutionError as exc:
            return AdapterResult(
                ok=False,
                exit_code=None,
                stdout="",
                stderr="",
                error=str(exc),
                metadata={"cwd": str(workdir_raw), "boundary": str(sandbox_root)},
            )

        base_args = entry.get("args") or entry.get("argv") or []
        if not isinstance(base_args, list):
            base_args = []
        cmd = [str(command), *[str(a) for a in base_args]]
        if argv:
            cmd.extend(str(a) for a in argv)

        timeout = timeout_seconds
        if timeout is None:
            timeout = resolved.descriptor.timeout_seconds
        if timeout is None:
            timeout = self.default_timeout_seconds

        try:
            result = run_confined(
                cmd,
                workspace=sandbox_root,
                cwd=workdir,
                env=env,
                timeout_seconds=float(timeout),
                input_text=input_text,
            )
        except ConfinedExecutionError as exc:
            return AdapterResult(
                ok=False,
                exit_code=None,
                stdout="",
                stderr="",
                error=str(exc),
                metadata={"cwd": str(workdir), "cmd": cmd, "boundary": str(sandbox_root)},
            )

        return AdapterResult(
            ok=result.exit_code == 0 and not result.timed_out and result.error is None,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
            error=result.error,
            metadata={
                **result.metadata,
                "network_isolation": result.network_isolation,
            },
        )


class ServerAdapter:
    """Remote/server-side tool profile — explicitly disabled until implemented."""

    kind = "server"
    ENABLED = False
    DISABLED_REASON = (
        "ServerAdapter profile is disabled until live remote invocation is implemented "
        "(wave-5: unsupported profile fail-closed)"
    )

    def invoke(self, *args: Any, **kwargs: Any) -> AdapterResult:
        del args, kwargs
        return AdapterResult(
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            error=self.DISABLED_REASON,
            metadata={"adapter": self.kind, "enabled": False},
        )
