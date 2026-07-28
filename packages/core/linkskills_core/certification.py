"""Certification evidence policy: refuse prompt-only and suite-authored fixtures.

Executed evidence must be receipt-bound: sealed executor ``execution_receipt``
objects with ``evidence_source == "executor"`` AND trusted Eval Runner issuer
provenance (HMAC). Bare output strings, artifacts, self-hashed-only receipts,
or tool traces without executor provenance never certify.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence


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
    "network_isolation",
    "provenance_kind",
    "issuer_id",
    "issuer_signature",
)

_TRUSTED_PROVENANCE = frozenset({"eval_runner_hmac_v1"})
_CERTIFIABLE_NETWORK_ISOLATION = "denied"


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _trusted_issuer_keys() -> list[bytes]:
    keys: list[bytes] = []
    primary = os.environ.get("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", "").strip()
    if primary:
        keys.append(primary.encode("utf-8"))
    extra = os.environ.get("LINKSKILLS_EVAL_RUNNER_TRUSTED_KEYS", "").strip()
    if extra:
        for part in extra.split(","):
            part = part.strip()
            if part:
                keys.append(part.encode("utf-8"))
    return keys


def _verify_issuer_signature(receipt_hash: str, signature: str) -> bool:
    if not receipt_hash or not signature:
        return False
    for key in _trusted_issuer_keys():
        expected = hmac.new(key, receipt_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, signature):
            return True
    return False


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
        "issuer_id": receipt.get("issuer_id"),
        "network_isolation": receipt.get("network_isolation"),
        "provenance_kind": receipt.get("provenance_kind"),
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
    """True only for a sealed, issuer-signed, isolation-proven executor receipt.

    ``allow_unproven`` local runs may mint receipts with
    ``network_isolation="unproven"``; those must never certify.
    """
    if not isinstance(receipt, Mapping):
        return False
    for key in _RECEIPT_REQUIRED_KEYS:
        if key not in receipt:
            return False
    if receipt.get("evidence_source") != "executor":
        return False
    if str(receipt.get("provenance_kind") or "") not in _TRUSTED_PROVENANCE:
        return False
    if not str(receipt.get("issuer_id") or "").strip():
        return False
    if str(receipt.get("network_isolation") or "") != _CERTIFIABLE_NETWORK_ISOLATION:
        return False
    claimed = str(receipt.get("receipt_hash") or "")
    if not claimed:
        return False
    release = str(receipt.get("skill_release_hash") or "").strip()
    if not release or release in {"skill-release:unset", "unset", "placeholder"}:
        return False
    expected = _sha256_text(_canonical_json(_receipt_payload_for_hash(receipt)))
    if claimed != expected:
        return False
    return _verify_issuer_signature(claimed, str(receipt.get("issuer_signature") or ""))


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

    for key in _SUITE_AUTHORED_ONLY:
        if key in case and case[key] not in (None, "", [], {}):
            pass
    return True


def evidence_is_executed(evidence: Mapping[str, Any]) -> bool:
    """Return True only when evidence includes sealed executor receipts."""
    return evaluate_certification_evidence(evidence).allowed


def evaluate_certification_evidence(evidence: Mapping[str, Any] | None) -> CertificationDecision:
    """Refuse certification when evidence lacks trusted executor receipts."""
    if not evidence:
        return CertificationDecision(False, "missing certification evidence")

    if evidence.get("prompt_only") is True:
        return CertificationDecision(False, "prompt-only scoring cannot certify")

    if evidence.get("suite_authored_as_evidence") is True:
        return CertificationDecision(
            False,
            "suite-authored outputs cannot authorize certification",
        )

    if not _trusted_issuer_keys():
        return CertificationDecision(
            False,
            "no trusted Eval Runner issuer key configured "
            "(LINKSKILLS_EVAL_RUNNER_ISSUER_KEY)",
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
            "evidence lacks trusted Eval Runner issuer-signed receipts",
        )

    if executed < len([c for c in cases if isinstance(c, Mapping)]):
        return CertificationDecision(
            False,
            "evidence includes cases without trusted issuer-signed receipts",
        )

    return CertificationDecision(
        True,
        f"accepted: {executed} trusted Eval Runner receipt(s) present",
    )
