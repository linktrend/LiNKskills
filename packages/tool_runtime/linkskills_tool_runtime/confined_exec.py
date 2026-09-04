"""Fail-closed confined subprocess execution.

Guarantees (waves 5–7):
- sanitized allowlisted environment (no caller ambient env passthrough);
- canonical realpath filesystem boundary with symlink-escape rejection;
- argv-only execution (no shell / no ``bash -lc``);
- network + filesystem isolation only when an OS isolator can **prove** both;
- certifiable ``network_isolation="denied"`` requires genuine path-allowlisted
  FS confidentiality (never a global file-read + short deny list);
- bounded CPU/time/output/process behavior.

See ADR 0009.
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
        # Stable downstream idempotency propagation (wave 9/10); not a secret.
        "LINKSKILLS_DOWNSTREAM_IDEMPOTENCY_KEY",
    }
)

# Minimal PATH for confined runs (no ambient user PATH).
# Include /usr/local/bin for container Python images (python:*-slim) while
# keeping PATH allowlisted and short — never inherit ambient host PATH.
_SAFE_PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

_DARWIN_RUNTIME_ROOTS = (
    "/usr",
    "/System",
    "/Library",
    "/opt/homebrew",
    "/opt/local",
    "/usr/local",
    "/dev",
    "/private/var/db/dyld",
    "/var/db/dyld",
)

_LINUX_RUNTIME_ROOTS = (
    "/usr",
    "/lib",
    "/lib64",
    "/bin",
    "/sbin",
    "/etc/ld.so.cache",
    "/etc/ssl",
    "/etc/pki",
    "/etc/passwd",
    "/etc/group",
    "/etc/nsswitch.conf",
)


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


def _sb_escape(path: str) -> str:
    return path.replace("\\", "\\\\").replace('"', '\\"')


def collect_runtime_read_paths(
    argv: Sequence[str],
    *,
    workspace: Path,
    env: Optional[Mapping[str, str]] = None,
) -> list[Path]:
    """Canonical realpaths the confined process may read (no host-wide /)."""
    roots: list[Path] = []
    seen: set[str] = set()

    def add(raw: Union[str, Path, None]) -> None:
        if raw is None:
            return
        path = Path(raw)
        if not path.is_absolute():
            # Relative paths are not host roots; skip unless they exist under cwd later.
            return
        if not path.exists():
            return
        # Keep both the nominal path and its realpath. On Debian/Ubuntu, ``/lib``
        # often symlinks to ``usr/lib``; ELF interpreters still look up
        # ``/lib/ld-linux-*.so.1``, so binding only the realpath leaves that
        # lookup path missing inside bwrap (execve → ENOENT).
        candidates = [path]
        try:
            resolved = _realpath(path)
            if resolved != path:
                candidates.append(resolved)
        except (OSError, RuntimeError):
            pass
        for candidate in candidates:
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            roots.append(candidate)

    add(workspace)
    exe = str(argv[0])
    resolved_exe = shutil.which(exe) if not os.path.isabs(exe) else exe
    if resolved_exe:
        # Bind the executable's directory, not the executable path itself.
        # Container Python commonly exposes /usr/local/bin/python* as symlinks;
        # bwrap rejects a nested bind whose destination is a symlink even when
        # the already-bound parent directory contains the executable safely.
        add(Path(resolved_exe).parent)
    for prefix in (sys.prefix, getattr(sys, "base_prefix", sys.prefix), sys.exec_prefix):
        add(prefix)
    if sys.platform == "darwin":
        for root in _DARWIN_RUNTIME_ROOTS:
            add(root)
    else:
        for root in _LINUX_RUNTIME_ROOTS:
            add(root)
    for key in ("SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        add(os.environ.get(key))
    if env:
        for key in ("SSL_CERT_FILE", "SSL_CERT_DIR", "PYTHONHOME", "VIRTUAL_ENV"):
            add(env.get(key))
        pythonpath = env.get("PYTHONPATH") or ""
        for part in pythonpath.split(os.pathsep):
            part = part.strip()
            if part:
                add(part)
    extra = os.environ.get("LINKSKILLS_EXECUTOR_EXTRA_RO_PATHS", "")
    for part in extra.split(os.pathsep):
        part = part.strip()
        if part:
            add(part)
    return roots


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _profile_uses_global_file_read(profile: str) -> bool:
    """True when a Seatbelt profile grants unrestricted file-read*."""
    # Bare ``(allow file-read*)`` with no path filter is global host read.
    for line in profile.splitlines():
        stripped = line.strip()
        if stripped == "(allow file-read*)":
            return True
    return False


def _darwin_allowlist_profile(
    *,
    workspace: Path,
    read_paths: Sequence[Path],
) -> str:
    """Pure path-allowlisted Seatbelt profile (no global file-read*)."""
    clauses: list[str] = []
    seen: set[str] = set()
    for path in [workspace, *read_paths]:
        if not path.exists():
            continue
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.is_dir():
            clauses.append(f'  (subpath "{_sb_escape(str(path))}")')
        else:
            clauses.append(f'  (literal "{_sb_escape(str(path))}")')
    allow_block = "\n".join(clauses)
    return f"""(version 1)
(deny default)
(allow process*)
(allow sysctl-read)
(allow mach*)
(allow file-read-metadata)
(allow file-read*
{allow_block}
)
(allow file-write*
  (subpath "{_sb_escape(str(workspace))}")
)
(deny network*)
"""


def _darwin_allowlist_boots(
    sandbox: str,
    profile_path: Path,
    argv: Sequence[str],
    *,
    workspace: Path,
    env: Mapping[str, str],
) -> bool:
    """Return True only when the allowlisted profile can start the interpreter."""
    probe_argv = [str(a) for a in argv]
    # Prefer a tiny Python probe when argv is python*; otherwise probe the binary.
    exe_name = Path(probe_argv[0]).name
    if exe_name.startswith("python"):
        probe_cmd = [sandbox, "-f", str(profile_path), probe_argv[0], "-c", "print('BOOT_OK')"]
    else:
        probe_cmd = [sandbox, "-f", str(profile_path), probe_argv[0], "--version"]
    try:
        completed = subprocess.run(
            probe_cmd,
            cwd=str(workspace),
            env=dict(env),
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if completed.returncode != 0:
        return False
    if exe_name.startswith("python"):
        return "BOOT_OK" in (completed.stdout or "")
    return True


def _resolve_argv0(argv0: str) -> str:
    """Resolve argv[0] to an absolute executable path when possible.

    Relative names (``python3``) must become absolute before bwrap/sandbox
    launch: sanitized PATH may omit the host directory where ``which`` found
    the binary (common with container Pythons under ``/usr/local/bin``).
    """
    if not argv0:
        return argv0
    if os.path.isabs(argv0):
        return argv0
    resolved = shutil.which(argv0)
    return resolved or argv0


def _ephemeral_sandbox_profile_path() -> Path:
    """Allocate a seatbelt profile path under system temp (never under workspace).

    Workspace is frequently the tool package directory that ``source_hash``
    walks; writing ``tmp/fs-allowlist.sb`` there contaminated clean-archive
    reproducibility.
    """
    state_root = Path(tempfile.gettempdir()) / "linkskills-confine-state"
    state_root.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(
        prefix="fs-allowlist-",
        suffix=".sb",
        dir=str(state_root),
    )
    os.close(handle)
    return Path(name)


def _wrap_with_network_deny(
    argv: Sequence[str],
    *,
    workspace: Path,
    env: Optional[Mapping[str, str]] = None,
) -> tuple[list[str], str]:
    """Prefer an OS isolator with proven path-scoped FS + network deny.

    Returns ``(argv, status)`` where status is:
    - ``denied`` — FS confidentiality + network denial are actually enforced
    - ``unavailable`` — no proven isolator (caller may stamp ``unproven``)
    """
    cmd = [str(a) for a in argv]
    if cmd:
        cmd[0] = _resolve_argv0(cmd[0])
    system = sys.platform
    read_paths = collect_runtime_read_paths(cmd, workspace=workspace, env=env)

    if system == "darwin":
        sandbox = shutil.which("sandbox-exec")
        if sandbox:
            # Wave 7: only claim ``denied`` for a genuine path allowlist.
            # Global ``(allow file-read*)`` + short deny list leaks /var/folders
            # and must never produce a certifiable receipt.
            profile = _darwin_allowlist_profile(workspace=workspace, read_paths=read_paths)
            if _profile_uses_global_file_read(profile):
                return cmd, "unavailable"
            # Never write seatbelt profiles under workspace (often the tool package
            # tree that source_hash walks). Keep them in ephemeral system state.
            profile_path = _ephemeral_sandbox_profile_path()
            profile_path.write_text(profile, encoding="utf-8")
            probe_env = dict(env or sanitize_env(workspace=workspace))
            if _darwin_allowlist_boots(
                sandbox, profile_path, cmd, workspace=workspace, env=probe_env
            ):
                return [sandbox, "-f", str(profile_path), *cmd], "denied"
            # dyld/shared-cache typically aborts (-6) under pure allowlists on
            # current macOS — refuse to claim denied; caller marks unproven.
            return cmd, "unavailable"

    if system.startswith("linux"):
        bwrap = shutil.which("bwrap")
        if bwrap:
            wrapped = [
                bwrap,
                "--unshare-net",
                "--die-with-parent",
                "--tmpfs",
                "/",
                "--dev",
                "/dev",
                "--proc",
                "/proc",
                "--tmpfs",
                "/tmp",
            ]
            # Parents first, then nested mounts (e.g. /usr then /usr/local) so
            # Docker nested mount points are not hidden by a parent bind.
            bind_paths = []
            for path in read_paths:
                if path == workspace or _is_under(path, workspace):
                    continue
                if not path.exists():
                    continue
                # Never re-introduce a host-wide root bind.
                if str(path) == "/":
                    continue
                bind_paths.append(path)
            bind_paths.sort(key=lambda p: (len(str(p)), str(p)))
            for path in bind_paths:
                wrapped.extend(["--ro-bind", str(path), str(path)])
            wrapped.extend(
                [
                    "--bind",
                    str(workspace),
                    str(workspace),
                    "--chdir",
                    str(workspace),
                    *cmd,
                ]
            )
            return wrapped, "denied"
        # unshare --net alone does not provide filesystem confidentiality.

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

    wrapped, isolation = _wrap_with_network_deny(
        [str(a) for a in argv], workspace=boundary, env=clean_env
    )
    if isolation != "denied":
        if _network_isolation_mode() == "required":
            raise ConfinedExecutionError(
                "network/filesystem isolation unavailable; refusing execution "
                "(install bwrap with path-scoped binds, a bootable path-allowlist "
                "sandbox, or a container/VM isolator — see ADR 0009; "
                "set LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven only for local tests)"
            )
        # Local-test escape hatch — never certifiable.
        isolation = "unproven"

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
                "read_allowlist": [
                    str(p)
                    for p in collect_runtime_read_paths(
                        argv, workspace=boundary, env=clean_env
                    )
                ],
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
