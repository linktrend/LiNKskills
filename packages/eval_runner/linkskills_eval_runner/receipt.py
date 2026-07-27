"""Immutable execution receipts for certification."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence


EXECUTOR_VERSION = "linkskills-eval-executor/0.2.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass
class ToolCallRecord:
    """One packaged-tool or command invocation observed by the executor."""

    tool_id: str
    version: str
    tool_hash: str
    adapter_kind: str
    argv: list[str] = field(default_factory=list)
    exit_code: Optional[int] = None
    stdout_hash: str = ""
    stderr_hash: str = ""
    timed_out: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionReceipt:
    """Immutable binding of case execution evidence for certification.

    Suite-authored ``observed_output`` / ``fixture_output`` values are never
    sufficient to mint a receipt. Only the executor may create receipts after a
    real workspace invocation.
    """

    receipt_id: str
    case_id: str
    skill_id: str
    suite_id: str
    suite_hash: str
    skill_release_hash: str
    execution_profile_hash: str
    environment: dict[str, Any]
    toolchain: dict[str, Any]
    tool_calls: list[ToolCallRecord]
    exit_code: Optional[int]
    stdout_hash: str
    stderr_hash: str
    artifact_hashes: list[str]
    started_at: str
    finished_at: str
    executor_version: str = EXECUTOR_VERSION
    evidence_source: str = "executor"
    receipt_hash: str = ""

    def payload_for_hash(self) -> dict[str, Any]:
        return {
            "artifact_hashes": list(self.artifact_hashes),
            "case_id": self.case_id,
            "environment": dict(self.environment),
            "evidence_source": self.evidence_source,
            "execution_profile_hash": self.execution_profile_hash,
            "executor_version": self.executor_version,
            "exit_code": self.exit_code,
            "finished_at": self.finished_at,
            "receipt_id": self.receipt_id,
            "skill_id": self.skill_id,
            "skill_release_hash": self.skill_release_hash,
            "started_at": self.started_at,
            "stderr_hash": self.stderr_hash,
            "stdout_hash": self.stdout_hash,
            "suite_hash": self.suite_hash,
            "suite_id": self.suite_id,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "toolchain": dict(self.toolchain),
        }

    def seal(self) -> "ExecutionReceipt":
        """Compute and attach the immutable receipt_hash."""
        self.receipt_hash = sha256_text(canonical_json(self.payload_for_hash()))
        return self

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_for_hash()
        payload["receipt_hash"] = self.receipt_hash
        return payload

    def verify_integrity(self) -> bool:
        if not self.receipt_hash:
            return False
        return self.receipt_hash == sha256_text(canonical_json(self.payload_for_hash()))


def default_environment() -> dict[str, Any]:
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "executor_version": EXECUTOR_VERSION,
    }


def build_execution_receipt(
    *,
    case_id: str,
    skill_id: str,
    suite_id: str,
    suite_hash: str,
    skill_release_hash: str,
    execution_profile_hash: str,
    toolchain: Optional[Mapping[str, Any]],
    tool_calls: Sequence[ToolCallRecord],
    exit_code: Optional[int],
    stdout: str,
    stderr: str,
    artifact_hashes: Sequence[str],
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    environment: Optional[Mapping[str, Any]] = None,
) -> ExecutionReceipt:
    """Mint a sealed receipt from executor-collected evidence."""
    started = started_at or _utc_now()
    finished = finished_at or _utc_now()
    receipt = ExecutionReceipt(
        receipt_id=str(uuid.uuid4()),
        case_id=case_id,
        skill_id=skill_id,
        suite_id=suite_id,
        suite_hash=suite_hash,
        skill_release_hash=skill_release_hash,
        execution_profile_hash=execution_profile_hash,
        environment=dict(environment or default_environment()),
        toolchain=dict(toolchain or {}),
        tool_calls=list(tool_calls),
        exit_code=exit_code,
        stdout_hash=sha256_text(stdout),
        stderr_hash=sha256_text(stderr),
        artifact_hashes=sorted(str(h) for h in artifact_hashes),
        started_at=started,
        finished_at=finished,
    )
    return receipt.seal()
