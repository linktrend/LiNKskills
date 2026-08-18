"""Immutable execution receipts for certification.

Wave 5: receipts are sealed with a content hash AND an Eval Runner issuer
HMAC (``LINKSKILLS_EVAL_RUNNER_ISSUER_KEY``). Self-hashed-only receipts are
insufficient for certification — see ``linkskills_core.certification``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import platform
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence


EXECUTOR_VERSION = "linkskills-eval-executor/0.4.0"
PROVENANCE_KIND = "eval_runner_hmac_v1"
DEFAULT_ISSUER_ID = "linkskills-eval-runner"
# Receipts with any value other than "denied" are not certifiable.
CERTIFIABLE_NETWORK_ISOLATION = "denied"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def issuer_signing_key() -> Optional[bytes]:
    raw = os.environ.get("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", "").strip()
    if not raw:
        return None
    return raw.encode("utf-8")


def issuer_id() -> str:
    return (
        os.environ.get("LINKSKILLS_EVAL_RUNNER_ISSUER_ID", "").strip() or DEFAULT_ISSUER_ID
    )


def sign_receipt_hash(receipt_hash: str, *, key: Optional[bytes] = None) -> str:
    material = key if key is not None else issuer_signing_key()
    if not material:
        raise RuntimeError(
            "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY is required to seal trusted receipts"
        )
    return hmac.new(material, receipt_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_issuer_signature(
    receipt_hash: str,
    signature: str,
    *,
    key: Optional[bytes] = None,
) -> bool:
    material = key if key is not None else issuer_signing_key()
    if not material or not signature:
        return False
    _bind = {"key": material}
    expected = sign_receipt_hash(receipt_hash, **_bind)
    return hmac.compare_digest(expected, signature)


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
    """Immutable binding of case execution evidence for certification."""

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
    network_isolation: str = "unavailable"
    receipt_hash: str = ""
    provenance_kind: str = PROVENANCE_KIND
    issuer_id: str = ""
    issuer_signature: str = ""

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
            "issuer_id": self.issuer_id,
            "network_isolation": self.network_isolation,
            "provenance_kind": self.provenance_kind,
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

    def seal(self, *, signing_key: Optional[bytes] = None) -> "ExecutionReceipt":
        """Attach content hash + Eval Runner issuer HMAC provenance."""
        if not self.issuer_id:
            self.issuer_id = issuer_id()
        self.provenance_kind = PROVENANCE_KIND
        self.receipt_hash = sha256_text(canonical_json(self.payload_for_hash()))
        self.issuer_signature = sign_receipt_hash(
            self.receipt_hash, key=signing_key
        )
        return self

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_for_hash()
        payload["receipt_hash"] = self.receipt_hash
        payload["issuer_signature"] = self.issuer_signature
        return payload

    def verify_integrity(self, *, signing_key: Optional[bytes] = None) -> bool:
        if not self.receipt_hash or not self.issuer_signature:
            return False
        if self.receipt_hash != sha256_text(canonical_json(self.payload_for_hash())):
            return False
        return verify_issuer_signature(
            self.receipt_hash, self.issuer_signature, key=signing_key
        )


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
    network_isolation: str = "unavailable",
    signing_key: Optional[bytes] = None,
) -> ExecutionReceipt:
    """Mint a sealed, issuer-signed receipt from executor-collected evidence."""
    started = started_at or _utc_now()
    finished = finished_at or _utc_now()
    isolation = str(network_isolation or "unavailable").strip() or "unavailable"
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
        network_isolation=isolation,
        issuer_id=issuer_id(),
    )
    return receipt.seal(signing_key=signing_key)
