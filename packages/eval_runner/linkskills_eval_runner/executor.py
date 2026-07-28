"""Real case executor boundary — runs tools/commands in an isolated workspace.

Suite-authored ``observed_output`` / ``fixture_output`` fields are NEVER treated
as executed evidence. They may only be used as golden/expected fixtures for
assertions after a real invocation.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

from .models import EvalCase, EvalSuite
from .receipt import (
    ExecutionReceipt,
    ToolCallRecord,
    build_execution_receipt,
    default_environment,
    sha256_text,
)
from .workspace import EvalWorkspace


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_root_guess() -> Path:
    # packages/eval_runner/linkskills_eval_runner/executor.py -> repo root
    return Path(__file__).resolve().parents[3]


@dataclass
class ExecutionCapture:
    """Raw capture from a single case execution."""

    ok: bool
    exit_code: Optional[int]
    stdout: str
    stderr: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    artifact_paths: list[Path] = field(default_factory=list)
    artifact_hashes: list[str] = field(default_factory=list)
    error: Optional[str] = None
    started_at: str = ""
    finished_at: str = ""
    receipt: Optional[ExecutionReceipt] = None

    @property
    def observed_output(self) -> str:
        return self.stdout


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(_file_hash(path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


UNSET_SKILL_RELEASE_HASH = "skill-release:unset"
UNSET_SKILL_RELEASE_MARKERS = frozenset(
    {
        "",
        UNSET_SKILL_RELEASE_HASH,
        "unset",
        "placeholder",
        "TODO",
        "null",
        "none",
        "skill-release:placeholder",
    }
)


def is_unset_skill_release_hash(value: Optional[str]) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    return text.lower() in {m.lower() for m in UNSET_SKILL_RELEASE_MARKERS}


def compute_skill_release_hash(skill_dir: Optional[Path]) -> str:
    """Hash an immutable skill-release directory tree.

    Missing directories yield the explicit unset marker. Certification must reject
    that marker — callers that intend to certify must supply a real release.
    """
    if skill_dir is None or not skill_dir.is_dir():
        return UNSET_SKILL_RELEASE_HASH
    return f"skill-release:{_hash_tree(skill_dir)}"


def _stable_execute_spec(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize execute blocks for profile identity (no absolute/temp paths)."""
    execute = dict(raw.get("execute") or {})
    if not execute:
        return {}
    stable: dict[str, Any] = {}
    for key in sorted(execute.keys()):
        if key in {"cwd", "workspace", "workdir", "env", "env_vars"}:
            continue
        value = execute[key]
        if key in {"tool_dir", "command"} and isinstance(value, str):
            # Keep relative identity only; strip absolute repo/tmp prefixes.
            path = Path(value)
            stable[key] = path.as_posix() if not path.is_absolute() else path.name
        else:
            stable[key] = value
    return stable


def compute_execution_profile_hash(
    *,
    suite: EvalSuite,
    toolchain: Mapping[str, Any],
    skill_release_hash: str,
) -> str:
    """Deterministic execution-profile identity.

    Excludes volatile temporary workspace paths, absolute repository paths,
    timestamps, UUIDs, and machine-specific environment details. Those may
    still appear on individual execution receipts.
    """
    cases = []
    for case in suite.cases:
        cases.append(
            {
                "assertions": case.raw.get("assertions") or {},
                "expected_criteria": list(case.expected_criteria),
                "execute": _stable_execute_spec(case.raw),
                "id": case.id,
                "input": case.input,
            }
        )
    payload = {
        "cases": cases,
        "pass_threshold": suite.pass_threshold,
        "rubric": [
            {
                "dimension": d.dimension,
                "hard_fail_below": d.hard_fail_below,
                "weight": d.weight,
            }
            for d in suite.rubric
        ],
        "skill_id": suite.skill_id,
        "skill_release_hash": skill_release_hash,
        "suite_hash": suite.suite_hash,
        "suite_id": suite.suite_id,
        "suite_version": suite.suite_version,
        "toolchain": dict(toolchain),
    }
    return sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def case_has_suite_authored_output(case: EvalCase) -> bool:
    return bool(case.raw.get("observed_output") is not None or case.raw.get("fixture_output") is not None)


def case_has_execute_block(case: EvalCase) -> bool:
    execute = case.raw.get("execute")
    return isinstance(execute, Mapping) and bool(execute.get("kind"))


def _resolve_tool_dir(spec: Mapping[str, Any], *, repo_root: Path, workspace: EvalWorkspace) -> Path:
    tool_dir = spec.get("tool_dir")
    tool_id = str(spec.get("tool_id") or "")
    if tool_dir:
        candidate = Path(str(tool_dir))
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        return candidate
    if tool_id:
        return (repo_root / "tools" / tool_id).resolve()
    raise ValueError("execute.packaged_tool requires tool_id or tool_dir")


def _execute_packaged_tool(
    spec: Mapping[str, Any],
    *,
    case: EvalCase,
    workspace: EvalWorkspace,
    repo_root: Path,
) -> tuple[int | None, str, str, ToolCallRecord, list[Path], str]:
    # Import lazily so eval_runner remains usable without tool_runtime on PYTHONPATH
    # in narrow unit tests — but certification canaries always include it.
    from linkskills_tool_runtime.invoke import invoke_tool
    from linkskills_tool_runtime.resolve import resolve_tool

    tool_dir = _resolve_tool_dir(spec, repo_root=repo_root, workspace=workspace)
    if not tool_dir.is_dir():
        raise FileNotFoundError(f"packaged tool directory not found: {tool_dir}")

    # Stage a copy into the isolated workspace so execution is sandboxed.
    staged = workspace.root / "tools" / tool_dir.name
    if staged.exists():
        shutil.rmtree(staged)
    shutil.copytree(tool_dir, staged)

    tool_id = str(spec.get("tool_id") or tool_dir.name)
    version = spec.get("version")
    bundle_hash = spec.get("bundle_hash") or spec.get("tool_hash")
    source_hash = spec.get("source_hash")
    argv = [str(a) for a in (spec.get("argv") or [])]
    # Allow case.input as trailing argv when requested.
    if spec.get("append_input_argv") and case.input:
        argv = [*argv, case.input.strip()]

    # Exact-hash gate for live execution: compute source hash if caller pinned none
    # but still require the resolved descriptor to expose a concrete hash after load.
    resolved = resolve_tool(
        staged,
        tool_id=tool_id,
        version=str(version) if version is not None else None,
        bundle_hash=str(bundle_hash) if bundle_hash is not None else None,
        source_hash=str(source_hash) if source_hash is not None else None,
    )
    # Prefer descriptor hash; fall back to staged tree hash for pin evidence.
    tool_hash = (
        resolved.bundle_hash
        or resolved.descriptor.source_hash
        or _hash_tree(staged)
    )

    timeout = spec.get("timeout_seconds")
    result = invoke_tool(
        staged,
        tool_id=tool_id,
        version=str(version) if version is not None else resolved.version,
        bundle_hash=str(bundle_hash) if bundle_hash is not None else resolved.bundle_hash,
        source_hash=str(source_hash) if source_hash is not None else resolved.descriptor.source_hash,
        argv=argv or None,
        cwd=staged,
        timeout_seconds=float(timeout) if timeout is not None else None,
        input_text=str(spec["stdin"]) if spec.get("stdin") is not None else None,
        adapter=str(spec.get("adapter") or "local"),
    )

    stdout_path = workspace.write_output(f"{case.id}.stdout", result.stdout or "")
    stderr_path = workspace.outputs_dir / f"{case.id}.stderr.txt"
    stderr_path.write_text(result.stderr or "", encoding="utf-8")
    call = ToolCallRecord(
        tool_id=result.tool_id,
        version=result.version,
        tool_hash=tool_hash,
        adapter_kind=result.adapter_kind,
        argv=argv,
        exit_code=result.exit_code,
        stdout_hash=sha256_text(result.stdout or ""),
        stderr_hash=sha256_text(result.stderr or ""),
        timed_out=result.timed_out,
        error=result.error,
    )
    isolation = str((result.metadata or {}).get("network_isolation") or "unavailable")
    return (
        result.exit_code,
        result.stdout or "",
        result.stderr or "",
        call,
        [stdout_path, stderr_path],
        isolation,
    )


def _execute_command(
    spec: Mapping[str, Any],
    *,
    case: EvalCase,
    workspace: EvalWorkspace,
) -> tuple[int | None, str, str, ToolCallRecord, list[Path], str]:
    from linkskills_tool_runtime.confined_exec import (
        ConfinedExecutionError,
        run_confined,
    )

    argv = [str(a) for a in (spec.get("argv") or [])]
    if not argv:
        raise ValueError("execute.command requires non-empty argv")
    if spec.get("append_input_argv") and case.input:
        argv = [*argv, case.input.strip()]
    timeout = float(spec.get("timeout_seconds") or 30)
    cwd: Path | str = workspace.root
    if spec.get("cwd"):
        cwd = workspace.root / str(spec["cwd"])
    try:
        confined = run_confined(
            argv,
            workspace=workspace.root,
            cwd=cwd,
            env={str(k): str(v) for k, v in dict(spec.get("env") or {}).items()},
            timeout_seconds=timeout,
            input_text=str(spec["stdin"]) if spec.get("stdin") is not None else None,
        )
        exit_code = confined.exit_code
        stdout = confined.stdout
        stderr = confined.stderr
        timed_out = confined.timed_out
        error = confined.error
        network_isolation = confined.network_isolation
    except ConfinedExecutionError as exc:
        exit_code = None
        stdout = ""
        stderr = ""
        timed_out = False
        error = str(exc)
        network_isolation = "unavailable"

    stdout_path = workspace.write_output(f"{case.id}.stdout", stdout)
    stderr_path = workspace.outputs_dir / f"{case.id}.stderr.txt"
    stderr_path.write_text(stderr, encoding="utf-8")
    call = ToolCallRecord(
        tool_id=str(spec.get("name") or argv[0]),
        version=str(spec.get("version") or "command"),
        tool_hash=sha256_text("\0".join(argv)),
        adapter_kind="confined_command",
        argv=argv,
        exit_code=exit_code,
        stdout_hash=sha256_text(stdout),
        stderr_hash=sha256_text(stderr),
        timed_out=timed_out,
        error=error,
    )
    return exit_code, stdout, stderr, call, [stdout_path, stderr_path], network_isolation


def execute_case(
    case: EvalCase,
    *,
    suite: EvalSuite,
    workspace: EvalWorkspace,
    toolchain: Optional[Mapping[str, Any]] = None,
    repo_root: Optional[Union[str, Path]] = None,
    skill_dir: Optional[Union[str, Path]] = None,
    skill_release_hash: Optional[str] = None,
) -> ExecutionCapture:
    """Execute one case via the real executor boundary and mint a receipt."""
    started = _utc_now()
    root = Path(repo_root) if repo_root else _repo_root_guess()
    toolchain_map = dict(toolchain or {})
    environment = default_environment()
    environment["workspace_root"] = str(workspace.root)
    environment["repo_root"] = str(root)

    if not case_has_execute_block(case):
        finished = _utc_now()
        return ExecutionCapture(
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            error=(
                "no execute block; suite-authored observed_output/fixture_output "
                "cannot substitute for execution"
            ),
            started_at=started,
            finished_at=finished,
        )

    execute = dict(case.raw.get("execute") or {})
    kind = str(execute.get("kind") or "").strip()
    network_isolation = "unavailable"
    try:
        if kind == "packaged_tool":
            exit_code, stdout, stderr, call, artifacts, network_isolation = _execute_packaged_tool(
                execute,
                case=case,
                workspace=workspace,
                repo_root=root,
            )
        elif kind == "command":
            exit_code, stdout, stderr, call, artifacts, network_isolation = _execute_command(
                execute,
                case=case,
                workspace=workspace,
            )
        else:
            finished = _utc_now()
            return ExecutionCapture(
                ok=False,
                exit_code=None,
                stdout="",
                stderr="",
                error=f"unsupported execute.kind: {kind!r}",
                started_at=started,
                finished_at=finished,
            )
    except Exception as exc:  # noqa: BLE001 — surface as infrastructure capture
        finished = _utc_now()
        return ExecutionCapture(
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            error=f"executor failure: {exc}",
            started_at=started,
            finished_at=finished,
        )

    finished = _utc_now()
    artifact_hashes = [_file_hash(path) for path in artifacts if path.is_file()]
    if skill_release_hash is not None:
        release_hash = str(skill_release_hash).strip()
    else:
        release_hash = compute_skill_release_hash(
            Path(skill_dir) if skill_dir else None
        )
    # Profile identity is deterministic across machines/runs; keep volatile
    # workspace/repo paths only on the individual receipt environment.
    profile_hash = compute_execution_profile_hash(
        suite=suite,
        toolchain=toolchain_map,
        skill_release_hash=release_hash,
    )
    environment["network_isolation"] = network_isolation
    receipt = build_execution_receipt(
        case_id=case.id,
        skill_id=suite.skill_id,
        suite_id=suite.suite_id,
        suite_hash=suite.suite_hash,
        skill_release_hash=release_hash,
        execution_profile_hash=profile_hash,
        toolchain=toolchain_map,
        tool_calls=[call],
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        artifact_hashes=artifact_hashes,
        started_at=started,
        finished_at=finished,
        environment=environment,
        network_isolation=network_isolation,
    )
    # Persist receipt into workspace evidence.
    receipt_path = workspace.evidence_dir / f"{case.id}.receipt.json"
    receipt_path.write_text(
        json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    ok = call.error is None and not call.timed_out and (exit_code == 0 or exit_code is not None)
    if call.timed_out or call.error:
        ok = False
    return ExecutionCapture(
        ok=ok,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        tool_calls=[call],
        artifact_paths=list(artifacts) + [receipt_path],
        artifact_hashes=artifact_hashes + [_file_hash(receipt_path)],
        error=call.error,
        started_at=started,
        finished_at=finished,
        receipt=receipt,
    )


# Keep a reference for tests that inspect interpreter path bindings.
PYTHON_EXECUTABLE = sys.executable
