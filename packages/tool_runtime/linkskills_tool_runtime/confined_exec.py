"""Fail-closed confined subprocess execution.

Guarantees (wave 5):
- sanitized allowlisted environment (no caller ambient env passthrough);
- canonical realpath filesystem boundary with symlink-escape rejection;
- argv-only execution (no shell / no ``bash -lc``);
- network denial when an OS isolator can prove it, otherwise refuse unless
  an explicit unproven-network escape hatch is set (certification rejects
  unproven receipts — see ADR 0009);
- bounded CPU/time/output/process behavior.
"""

from __future__ import annotations

import os
import resource
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence, Union


DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_OUTPUT_BYTES = 1_048_576  # 1 MiB per stream
DEFAULT_MAX_ADDRESS_BYTES = 512 * 1024 * 1024  # 512 MiB soft RSS hint (best-effort)
ALLOWED_ENV_KEYS = frozenset(
    {
        "PATH",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TZ",
        "TMPDIR",
        "TMP",
        "TEMP",
        "HOME",
        "USER",
        "LOGNAME",
        "TERM",
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONNOUSERSITE",
        "PYTHONIOENCODING",
        "VIRTUAL_ENV",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
        "SYSTEMROOT",  # Windows-safe no-op on Unix
    }
)

# Minimal PATH for confined runs (no ambient user PATH).
_SAFE_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"


class ConfinedExecutionError(RuntimeError):
    """Raised when confinement invariants cannot be satisfied (fail closed)."""


@dataclass
class ConfinedResult:
    exit_code: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool = False
    error: Optional[str] = None
    network_isolation: str = "unavailable"
    metadata: dict = field(default_factory=dict)


def _realpath(path: Path) -> Path:
    return Path(os.path.realpath(path))


def assert_within_boundary(path: Union[str, Path], boundary: Union[str, Path]) -> Path:
    """Resolve ``path`` and reject symlink escapes outside ``boundary``."""
    root = _realpath(Path(boundary))
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = _realpath(candidate)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ConfinedExecutionError(
            f"path escapes filesystem boundary: {resolved} not under {root}"
        ) from exc
    # Reject intermediate symlink escapes: walk parents and ensure each realpath
    # remains under the boundary when the path exists.
    probe = candidate if candidate.exists() else candidate.parent
    while True:
        probe_real = _realpath(probe)
        try:
            probe_real.relative_to(root)
        except ValueError as exc:
            raise ConfinedExecutionError(
                f"symlink escape rejected: {probe} -> {probe_real}"
            ) from exc
        if probe_real == root or probe == probe.parent:
            break
        probe = probe.parent
    return resolved


def sanitize_env(
    extra: Optional[Mapping[str, str]] = None,
    *,
    workspace: Path,
    allow_keys: Optional[frozenset[str]] = None,
) -> dict[str, str]:
    """Build a sanitized environment; ambient secrets are not inherited."""
    allowed = allow_keys or ALLOWED_ENV_KEYS
    env: dict[str, str] = {
        "PATH": _SAFE_PATH,
        "HOME": str(workspace),
        "TMPDIR": str(workspace / "tmp"),
        "TMP": str(workspace / "tmp"),
        "TEMP": str(workspace / "tmp"),
        "LANG": os.environ.get("LANG") or "C.UTF-8",
        "LC_ALL": os.environ.get("LC_ALL") or "C.UTF-8",
        "PYTHONNOUSERSITE": "1",
        "PYTHONIOENCODING": "utf-8",
        # Deny common proxy/network helpers unless isolation is proven separately.
        "http_proxy": "",
        "https_proxy": "",
        "HTTP_PROXY": "",
        "HTTPS_PROXY": "",
        "ALL_PROXY": "",
        "all_proxy": "",
        "NO_PROXY": "*",
        "no_proxy": "*",
    }
    # Carry only allowlisted non-secret interpreter settings from the host.
    for key in ("SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        if key in os.environ and key in allowed:
            env[key] = os.environ[key]
    if extra:
        for key, value in extra.items():
            name = str(key)
            if name not in allowed:
                raise ConfinedExecutionError(
                    f"environment key not allowlisted: {name}"
                )
            env[name] = str(value)
    (workspace / "tmp").mkdir(parents=True, exist_ok=True)
    return env


def _truncate(text: str, limit: int) -> str:
    if len(text.encode("utf-8", errors="replace")) <= limit:
        return text
    # Truncate by characters with a marker; byte-accurate trim is best-effort.
    encoded = text.encode("utf-8", errors="replace")[: max(0, limit - 64)]
    return encoded.decode("utf-8", errors="replace") + "\n[truncated:output_limit]\n"


def _resource_preexec(max_address_bytes: int, *, cpu_seconds: int) -> None:
    try:
        _soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        target = min(max_address_bytes, hard if hard > 0 else max_address_bytes)
        resource.setrlimit(resource.RLIMIT_AS, (target, hard if hard > 0 else target))
    except (ValueError, OSError, AttributeError):
        # Best-effort; platforms without RLIMIT_AS continue with time/output bounds.
        pass
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (max(1, cpu_seconds), max(1, cpu_seconds)))
    except (ValueError, OSError, AttributeError):
        pass
    try:
        os.setsid()
    except OSError:
        pass


def _network_isolation_mode() -> str:
    """Return ``required`` (default) or ``allow_unproven`` (local tests only)."""
    raw = os.environ.get("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "required").strip().lower()
    if raw in {"allow_unproven", "unproven", "0", "false", "off", "soft"}:
        return "allow_unproven"
    return "required"


def _wrap_with_network_deny(argv: Sequence[str], *, workspace: Path) -> tuple[list[str], str]:
    """Prefer an OS network-deny wrapper; return (argv, status)."""
    cmd = [str(a) for a in argv]
    system = sys.platform

    if system == "darwin":
        sandbox = shutil.which("sandbox-exec")
        if sandbox:
            profile = f"""(version 1)
(deny default)
(allow process*)
(allow sysctl-read)
(allow mach*)
(allow file-read*)
(allow file-write* (subpath "{workspace}"))
(allow file-write* (subpath "/private/tmp"))
(allow file-write* (subpath "/tmp"))
(deny network*)
"""
            profile_path = workspace / "tmp" / "network-deny.sb"
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(profile, encoding="utf-8")
            return [sandbox, "-f", str(profile_path), *cmd], "denied"

    if system.startswith("linux"):
        bwrap = shutil.which("bwrap")
        if bwrap:
            return [
                bwrap,
                "--unshare-net",
                "--die-with-parent",
                "--ro-bind",
                "/",
                "/",
                "--bind",
                str(workspace),
                str(workspace),
                "--dev",
                "/dev",
                "--proc",
                "/proc",
                "--tmpfs",
                "/tmp",
                "--chdir",
                str(workspace),
                *cmd,
            ], "denied"
        unshare = shutil.which("unshare")
        if unshare:
            return [unshare, "--net", "--map-root-user", *cmd], "denied"

    return cmd, "unavailable"


def run_confined(
    argv: Sequence[str],
    *,
    workspace: Union[str, Path],
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout_seconds: Optional[float] = None,
    input_text: Optional[str] = None,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
    max_address_bytes: int = DEFAULT_MAX_ADDRESS_BYTES,
) -> ConfinedResult:
    """Run ``argv`` under fail-closed confinement."""
    if not argv:
        raise ConfinedExecutionError("argv must be non-empty")
    if any(not str(a) for a in argv):
        raise ConfinedExecutionError("argv entries must be non-empty strings")
    # Reject shell metacharacter smuggling via a single shell string.
    if len(argv) == 1 and any(ch in str(argv[0]) for ch in (";", "|", "&", "`", "\n")):
        raise ConfinedExecutionError("shell metacharacters rejected; pass argv list")
    for banned in ("bash", "sh", "zsh", "dash", "csh", "ksh"):
        if Path(str(argv[0])).name == banned and len(argv) >= 2 and str(argv[1]) in {
            "-c",
            "-lc",
            "-cl",
        }:
            raise ConfinedExecutionError("unrestricted shell execution is forbidden")

    boundary = _realpath(Path(workspace))
    if not boundary.is_dir():
        raise ConfinedExecutionError(f"workspace boundary is not a directory: {boundary}")

    workdir = assert_within_boundary(cwd or boundary, boundary)
    clean_env = sanitize_env(env, workspace=boundary)

    timeout = float(timeout_seconds if timeout_seconds is not None else DEFAULT_TIMEOUT_SECONDS)
    if timeout <= 0 or timeout > 600:
        raise ConfinedExecutionError("timeout_seconds must be in (0, 600]")

    wrapped, isolation = _wrap_with_network_deny([str(a) for a in argv], workspace=boundary)
    if isolation != "denied" and _network_isolation_mode() == "required":
        raise ConfinedExecutionError(
            "network isolation unavailable; refusing execution "
            "(install sandbox-exec/bwrap or see ADR 0009; "
            "set LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven only for local tests)"
        )

    try:
        completed = subprocess.run(
            wrapped,
            cwd=str(workdir),
            env=clean_env,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            start_new_session=True,
            preexec_fn=(
                (
                    lambda: _resource_preexec(
                        max_address_bytes, cpu_seconds=max(1, int(timeout) + 1)
                    )
                )
                if os.name == "posix"
                else None
            ),
        )
        stdout = _truncate(completed.stdout or "", max_output_bytes)
        stderr = _truncate(completed.stderr or "", max_output_bytes)
        return ConfinedResult(
            exit_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            network_isolation=isolation,
            metadata={
                "cwd": str(workdir),
                "cmd": list(wrapped),
                "boundary": str(boundary),
            },
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return ConfinedResult(
            exit_code=None,
            stdout=_truncate(stdout, max_output_bytes),
            stderr=_truncate(stderr, max_output_bytes),
            timed_out=True,
            error=f"timed out after {timeout}s",
            network_isolation=isolation,
            metadata={"cwd": str(workdir), "cmd": list(wrapped), "boundary": str(boundary)},
        )
    except OSError as exc:
        return ConfinedResult(
            exit_code=None,
            stdout="",
            stderr="",
            error=str(exc),
            network_isolation=isolation,
            metadata={"cwd": str(workdir), "cmd": list(wrapped), "boundary": str(boundary)},
        )


def make_temp_workspace(prefix: str = "linkskills-confine-") -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))
