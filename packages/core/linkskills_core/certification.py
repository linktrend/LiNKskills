"""Certification evidence policy: refuse prompt-only and suite-authored fixtures.

Executed evidence must be receipt-bound: sealed executor ``execution_receipt``
objects with ``evidence_source == "executor"``. Bare output strings, artifacts,
or tool traces without executor provenance never certify.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class CertificationDecision:
    allowed: bool
    reason: str

    @property
    def refused(self) -> bool:
        return not self.allowed


# Suite-authored fixture keys — never sufficient as executed evidence alone.
_SUITE_AUTHORED_ONLY = frozenset(
    {
        "observed_output",
        "fixture_output",
        "expected_output",
        "golden_output",
    }
)

_RECEIPT_REQUIRED_KEYS = (
    "receipt_hash",
    "receipt_id",
    "case_id",
    "skill_id",
    "suite_id",
    "suite_hash",
    "skill_release_hash",
    "execution_profile_hash",
    "stdout_hash",
    "stderr_hash",
    "tool_calls",
    "environment",
    "evidence_source",
    "executor_version",
)


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _receipt_payload_for_hash(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Mirror eval-runner ExecutionReceipt.payload_for_hash (seal contract)."""
    tool_calls = receipt.get("tool_calls") or []
    normalized_calls: list[Any] = []
    for tc in tool_calls:
        if isinstance(tc, Mapping):
            normalized_calls.append(dict(tc))
        else:
            normalized_calls.append(tc)
    return {
        "artifact_hashes": list(receipt.get("artifact_hashes") or []),
        "case_id": receipt.get("case_id"),
        "environment": dict(receipt.get("environment") or {}),
        "evidence_source": receipt.get("evidence_source"),
        "execution_profile_hash": receipt.get("execution_profile_hash"),
        "executor_version": receipt.get("executor_version"),
        "exit_code": receipt.get("exit_code"),
        "finished_at": receipt.get("finished_at"),
        "receipt_id": receipt.get("receipt_id"),
        "skill_id": receipt.get("skill_id"),
        "skill_release_hash": receipt.get("skill_release_hash"),
        "started_at": receipt.get("started_at"),
        "stderr_hash": receipt.get("stderr_hash"),
        "stdout_hash": receipt.get("stdout_hash"),
        "suite_hash": receipt.get("suite_hash"),
        "suite_id": receipt.get("suite_id"),
        "tool_calls": normalized_calls,
        "toolchain": dict(receipt.get("toolchain") or {}),
    }


def sealed_executor_receipt(receipt: Any) -> bool:
    """True only for a sealed executor receipt with matching receipt_hash."""
    if not isinstance(receipt, Mapping):
        return False
    for key in _RECEIPT_REQUIRED_KEYS:
        if key not in receipt:
            return False
    if receipt.get("evidence_source") != "executor":
        return False
    claimed = str(receipt.get("receipt_hash") or "")
    if not claimed:
        return False
    release = str(receipt.get("skill_release_hash") or "").strip()
    if not release or release in {"skill-release:unset", "unset", "placeholder"}:
        return False
    expected = _sha256_text(_canonical_json(_receipt_payload_for_hash(receipt)))
    return claimed == expected


def _case_has_executed_output(case: Mapping[str, Any]) -> bool:
    """True when a case record includes sealed executor receipt evidence."""
    receipt = case.get("execution_receipt")
    source = case.get("evidence_source")

    evidence = case.get("evidence")
    if isinstance(evidence, Mapping):
        if receipt is None:
            receipt = evidence.get("execution_receipt")
        if source is None:
            source = evidence.get("evidence_source")

    if source != "executor":
        return False
    if not sealed_executor_receipt(receipt):
        return False

    # Suite-authored fields never substitute for a receipt.
    for key in _SUITE_AUTHORED_ONLY:
        if key in case and case[key] not in (None, "", [], {}):
            pass
    return True


def evidence_is_executed(evidence: Mapping[str, Any]) -> bool:
    """Return True only when evidence includes sealed executor receipts."""
    return evaluate_certification_evidence(evidence).allowed


def evaluate_certification_evidence(evidence: Mapping[str, Any] | None) -> CertificationDecision:
    """Refuse certification when evidence lacks sealed executor receipts.

    Prompt-only payloads, suite-authored observed_output/fixture_output, bare
    ``output`` / ``tool_traces`` / artifacts without executor provenance cannot
    certify an execution profile.
    """
    if not evidence:
        return CertificationDecision(False, "missing certification evidence")

    if evidence.get("prompt_only") is True:
        return CertificationDecision(False, "prompt-only scoring cannot certify")

    if evidence.get("suite_authored_as_evidence") is True:
        return CertificationDecision(
            False,
            "suite-authored outputs cannot authorize certification",
        )

    cases: Sequence[Any] | None = None
    for key in ("cases", "case_results", "executed_cases"):
        value = evidence.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            cases = value
            break

    if not cases:
        return CertificationDecision(
            False,
            "evidence lacks executed case outputs (no cases/case_results)",
        )

    executed = 0
    for raw in cases:
        if isinstance(raw, Mapping) and _case_has_executed_output(raw):
            executed += 1

    if executed == 0:
        return CertificationDecision(
            False,
            "evidence lacks sealed executor receipts (receipt-bound rejection)",
        )

    if executed < len([c for c in cases if isinstance(c, Mapping)]):
        return CertificationDecision(
            False,
            "evidence includes cases without sealed executor receipts",
        )

    return CertificationDecision(
        True,
        f"accepted: {executed} sealed executor receipt(s) present",
    )
