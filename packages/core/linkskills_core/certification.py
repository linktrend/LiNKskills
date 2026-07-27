"""Certification evidence policy: refuse prompt-only scoring."""

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


def _case_has_executed_output(case: Mapping[str, Any]) -> bool:
    """True when a case record includes executed outputs (not prompt/rubric-only)."""
    for key in (
        "executed_output",
        "output",
        "outputs",
        "observed_output",
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
    evidence = case.get("evidence")
    if isinstance(evidence, Mapping):
        for key in ("output", "outputs", "artifacts", "tool_traces"):
            value = evidence.get(key)
            if isinstance(value, str) and value.strip():
                return True
            if isinstance(value, (list, tuple, dict)) and len(value) > 0:
                return True
    return False


def evaluate_certification_evidence(evidence: Mapping[str, Any] | None) -> CertificationDecision:
    """Refuse certification when evidence lacks executed case outputs.

    Prompt-only payloads (suite ids, rubric names, thresholds, model scores without
    executed outputs) cannot certify an execution profile.
    """
    if not evidence:
        return CertificationDecision(False, "missing certification evidence")

    if evidence.get("prompt_only") is True:
        return CertificationDecision(False, "prompt-only scoring cannot certify")

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
