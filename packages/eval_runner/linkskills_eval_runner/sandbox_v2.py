"""Fail-closed policy checks for hostile imported evaluation candidates.

The sandbox planner is deliberately policy-only. It does not execute an
untrusted candidate, grant authority, or mutate a release pointer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Mapping


FORBIDDEN = frozenset(
    {
        "network",
        "subprocess",
        "secret_env",
        "symlink",
        "archive",
        "executable",
        "path_escape",
        "destructive",
        "production_mutation",
        "authority_escalation",
    }
)
KNOWN_EFFECTS = frozenset(
    {
        "stdout",
        "stderr",
        "workspace_read",
        "workspace_write",
        "tool_call",
        "network",
        "file_write",
        "file_delete",
        "destructive",
        "production_mutation",
    }
)
KNOWN_TRUST_BOUNDARIES = frozenset(
    {"untrusted_external", "trusted_internal", "synthetic_fixture"}
)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,239}$")


@dataclass(frozen=True)
class SandboxPlan:
    """Deterministic workspace policy for one candidate."""

    candidate_digest: str
    workspace_id: str
    network: str = "deny"
    cpu_seconds: int = 30
    memory_mb: int = 256
    output_bytes: int = 65536
    declared_effects: tuple[str, ...] = ()
    trust_boundary: str = "unknown"

    def evidence(self, evaluator: str, environment: str, policy: str) -> dict[str, Any]:
        """Return bounded evidence without candidate content or instructions."""
        return {
            "candidate_digest": self.candidate_digest,
            "evaluator_release": evaluator,
            "environment_profile": environment,
            "policy_version": policy,
            "workspace_id": self.workspace_id,
            "declared_effects": list(self.declared_effects),
            "trust_boundary": self.trust_boundary,
            "network": self.network,
        }


@dataclass(frozen=True)
class CandidateAssessment:
    """Bounded qualification result for imported or private-domain content."""

    candidate_digest: str
    outcome: str
    reasons: tuple[str, ...] = ()
    source_identity: Mapping[str, str] = field(default_factory=dict)
    release_identity: Mapping[str, str] = field(default_factory=dict)
    declared_effects: tuple[str, ...] = ()
    privacy_findings: tuple[str, ...] = ()

    @property
    def admitted(self) -> bool:
        """Whether the candidate may enter executed evaluation."""
        return self.outcome == "eligible_for_evaluation"

    def to_dict(self) -> dict[str, Any]:
        """Serialize only bounded qualification metadata."""
        return {
            "candidate_digest": self.candidate_digest,
            "outcome": self.outcome,
            "reasons": list(self.reasons),
            "source_identity": dict(self.source_identity),
            "release_identity": dict(self.release_identity),
            "declared_effects": list(self.declared_effects),
            "privacy_findings": list(self.privacy_findings),
        }


def _candidate_digest(candidate: Mapping[str, Any]) -> str:
    raw = json.dumps(candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"candidate:{field}_missing")
    return value.strip()


def _identity(identity: Any, *, kind: str) -> dict[str, str]:
    if not isinstance(identity, Mapping):
        raise ValueError(f"candidate:{kind}_identity_missing")
    required = {
        "source": ("source_ref", "source_commit", "source_path", "content_digest"),
        "release": ("release_id", "version", "artifact_digest", "content_digest"),
    }[kind]
    result = {name: _text(identity.get(name), f"{kind}_{name}") for name in required}
    if kind == "source" and not _COMMIT_RE.fullmatch(result["source_commit"]):
        raise ValueError("candidate:source_commit_invalid")
    digest_fields = ("artifact_digest", "content_digest") if kind == "release" else ("content_digest",)
    for name in digest_fields:
        if not _DIGEST_RE.fullmatch(result[name]):
            raise ValueError(f"candidate:{kind}_{name}_invalid")
    identity_name = result["release_id"] if kind == "release" else result["source_ref"]
    if not _SAFE_ID_RE.fullmatch(identity_name):
        raise ValueError(f"candidate:{kind}_identity_invalid")
    if kind == "source" and (
        result["source_path"].startswith("/")
        or ".." in result["source_path"].split("/")
        or "\\" in result["source_path"]
    ):
        raise ValueError("candidate:source_path_invalid")
    return result


def _security_metadata(
    candidate: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str], tuple[str, ...], tuple[str, ...], list[str]]:
    reasons: list[str] = []
    try:
        source = _identity(candidate.get("source_identity"), kind="source")
    except ValueError as exc:
        reasons.append(str(exc))
        source = {}
    try:
        release = _identity(candidate.get("release_identity"), kind="release")
    except ValueError as exc:
        reasons.append(str(exc))
        release = {}

    raw_effects = candidate.get("declared_effects")
    effects = (
        tuple(sorted({str(item).strip() for item in raw_effects if str(item).strip()}))
        if isinstance(raw_effects, (list, tuple, set))
        else ()
    )
    if not effects:
        reasons.append("candidate:declared_effects_missing")
    unknown_effects = sorted(set(effects) - KNOWN_EFFECTS)
    if unknown_effects:
        reasons.append("candidate:unknown_effect:" + ",".join(unknown_effects))
    forbidden_effects = sorted(set(effects) & FORBIDDEN)
    if forbidden_effects:
        reasons.append("candidate:forbidden_effect:" + ",".join(forbidden_effects))

    findings_raw = candidate.get("privacy_findings")
    if findings_raw is not None and not isinstance(findings_raw, (list, tuple)):
        reasons.append("candidate:privacy_findings_invalid")
    findings = (
        tuple(sorted(str(item).strip() for item in findings_raw if str(item).strip()))
        if isinstance(findings_raw, (list, tuple))
        else ()
    )
    if findings:
        reasons.append("candidate:privacy_findings")

    licence = candidate.get("licence", candidate.get("license"))
    licence_status = (
        str(licence.get("status") or licence.get("review_status") or "").strip().lower()
        if isinstance(licence, Mapping)
        else ""
    )
    if licence_status not in {"approved", "compatible", "reviewed", "not_required"}:
        reasons.append("candidate:licence_gap")
    if candidate.get("observed_content_digest") and release:
        if str(candidate["observed_content_digest"]).strip() != release.get("content_digest"):
            reasons.append("candidate:digest_drift")
    if str(candidate.get("compatibility") or "").strip().lower() != "compatible":
        reasons.append("candidate:compatibility_not_proven")
    boundary = str(candidate.get("trust_boundary") or "").strip()
    if boundary not in KNOWN_TRUST_BOUNDARIES:
        reasons.append("candidate:unknown_trust_boundary")
    if bool(candidate.get("active_production_mutation")) or "production_mutation" in effects:
        reasons.append("candidate:production_mutation_forbidden")
    return source, release, effects, findings, reasons


def assess_candidate(candidate: Mapping[str, Any]) -> CandidateAssessment:
    """Assess an imported candidate without executing it or changing state."""
    if not isinstance(candidate, Mapping):
        raise ValueError("candidate:object_required")
    digest = _candidate_digest(candidate)
    source, release, effects, findings, reasons = _security_metadata(candidate)
    outcome = "eligible_for_evaluation" if not reasons else "hold_quarantine"
    return CandidateAssessment(
        candidate_digest=digest,
        outcome=outcome,
        reasons=tuple(sorted(set(reasons))),
        source_identity=source,
        release_identity=release,
        declared_effects=effects,
        privacy_findings=findings,
    )


def plan_candidate(candidate: dict) -> SandboxPlan:
    """Create a legacy-compatible plan; hostile actions still fail closed."""
    actions = set(candidate.get("declared_actions", []))
    if actions & FORBIDDEN:
        raise ValueError("quarantine:forbidden_candidate_capability")
    for path in candidate.get("paths", []):
        if (
            not isinstance(path, str)
            or path.startswith("/")
            or ".." in path.split("/")
            or "\\" in path
        ):
            raise ValueError("quarantine:unsafe_path")
    digest = _candidate_digest(candidate)
    effects = tuple(sorted(str(item) for item in candidate.get("declared_effects", [])))
    return SandboxPlan(
        digest,
        "eval-" + digest[7:23],
        declared_effects=effects,
        trust_boundary=str(candidate.get("trust_boundary") or "unknown"),
    )


def qualification_outcome(signal: str) -> str:
    """Map hostile execution signals to a non-qualifying lifecycle outcome."""
    return "hold_quarantine" if signal in {"timeout", "crash", "escape", "cleanup_failure", "policy_denied"} else "evidence_pending_review"
