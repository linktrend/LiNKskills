"""Execution adapters for packaged tools."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

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
    """Run a tool as a local subprocess with timeout and cwd sandbox."""

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

        workdir_raw = cwd or entry.get("working_directory") or resolved.tool_dir
        workdir = Path(workdir_raw)
        if not workdir.is_absolute():
            workdir = (resolved.tool_dir / workdir).resolve()
        else:
            workdir = workdir.resolve()
        # Sandbox: cwd must remain under the resolved tool dir or an explicit caller cwd.
        sandbox_root = resolved.tool_dir.resolve()
        if cwd is None and not str(workdir).startswith(str(sandbox_root)):
            workdir = sandbox_root

        base_args = entry.get("args") or entry.get("argv") or []
        if not isinstance(base_args, list):
            base_args = []
        cmd: list[str]
        if argv:
            cmd = [str(command), *[str(a) for a in base_args], *[str(a) for a in argv]]
        else:
            # Allow command to be a full shell-ish string only when no argv provided.
            if isinstance(command, str) and " " in command and not base_args:
                cmd = ["bash", "-lc", command]
            else:
                cmd = [str(command), *[str(a) for a in base_args]]

        timeout = timeout_seconds
        if timeout is None:
            timeout = resolved.descriptor.timeout_seconds
        if timeout is None:
            timeout = self.default_timeout_seconds

        try:
            completed = subprocess.run(
                cmd,
                cwd=str(workdir),
                env=dict(env) if env is not None else None,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=float(timeout),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            return AdapterResult(
                ok=False,
                exit_code=None,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
                error=f"timed out after {timeout}s",
                metadata={"cwd": str(workdir), "cmd": cmd},
            )
        except OSError as exc:
            return AdapterResult(
                ok=False,
                exit_code=None,
                stdout="",
                stderr="",
                error=str(exc),
                metadata={"cwd": str(workdir), "cmd": cmd},
            )

        return AdapterResult(
            ok=completed.returncode == 0,
            exit_code=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            metadata={"cwd": str(workdir), "cmd": cmd},
        )


class ServerAdapter:
    """Stub for live remote/server-side tool execution."""

    kind = "server"

    def invoke(self, *args: Any, **kwargs: Any) -> AdapterResult:
        raise NotImplementedError(
            "ServerAdapter live remote invocation is not implemented in Phase 3"
        )
