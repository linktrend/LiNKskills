"""Certification evidence policy: refuse prompt-only and suite-authored fixtures."""

from __future__ import annotations

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


def _case_has_executed_output(case: Mapping[str, Any]) -> bool:
    """True when a case record includes real executed evidence (not suite fixtures)."""
    # Explicit executor receipt / evidence_source is authoritative.
    if case.get("evidence_source") == "executor" and case.get("execution_receipt"):
        return True
    receipt = case.get("execution_receipt")
    if isinstance(receipt, Mapping) and receipt.get("receipt_hash"):
        if receipt.get("evidence_source") == "executor" or case.get("evidence_source") == "executor":
            return True

    for key in (
        "executed_output",
        "output",
        "outputs",
        "case_output",
        "artifact_refs",
        "tool_results",
        "tool_traces",
    ):
        if key not in case:
            continue
        value = case[key]
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, (list, tuple, dict)) and len(value) > 0:
            return True

    # Suite-authored observed/fixture/expected/golden alone never count.
    for key in _SUITE_AUTHORED_ONLY:
        if key in case and case[key] not in (None, "", [], {}):
            # Present but insufficient without executor evidence above.
            pass

    evidence = case.get("evidence")
    if isinstance(evidence, Mapping):
        if evidence.get("evidence_source") == "executor" and evidence.get("execution_receipt"):
            return True
        for key in ("output", "outputs", "artifacts", "tool_traces", "executed_output"):
            value = evidence.get(key)
            if isinstance(value, str) and value.strip():
                return True
            if isinstance(value, (list, tuple, dict)) and len(value) > 0:
                return True
    return False


def evidence_is_executed(evidence: Mapping[str, Any]) -> bool:
    """Return True only when evidence includes executed (non-fixture) case outputs."""
    return evaluate_certification_evidence(evidence).allowed


def evaluate_certification_evidence(evidence: Mapping[str, Any] | None) -> CertificationDecision:
    """Refuse certification when evidence lacks executed case outputs.

    Prompt-only payloads and suite-authored observed_output/fixture_output
    alone cannot certify an execution profile.
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
            "evidence lacks executed case outputs (prompt-only rejection)",
        )

    return CertificationDecision(
        True,
        f"accepted: {executed} executed case output(s) present",
    )
