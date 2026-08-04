"""Shared test helpers (importable without relying on pytest conftest module path)."""

from __future__ import annotations

import tempfile
from pathlib import Path


def proven_executor_isolation_available() -> bool:
    """True when confined_exec can stamp certifiable network_isolation=denied."""
    from linkskills_tool_runtime.confined_exec import run_confined

    workspace = Path(tempfile.mkdtemp(prefix="linkskills-iso-probe-"))
    (workspace / "tmp").mkdir(exist_ok=True)
    result = run_confined(["python3", "-c", "print('iso')"], workspace=workspace)
    return result.network_isolation == "denied"
