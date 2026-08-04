"""Autonomy boundaries for the LiNKskills Librarian domain worker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence


FORBIDDEN_ACTIONS = frozenset(
    {
        "push_staging",
        "push_main",
        "direct_staging_push",
        "direct_main_push",
        "grant_permission",
        "grant_program_permission",
        "rewrite_published_immutable",
        "bypass_ci",
        "bypass_eval",
        "edit_linkplatform_runner",
        "apply_live_shared_migration",
        "auto_merge_low_confidence",
        "auto_split_low_confidence",
    }
)

PROTECTED_BRANCHES = frozenset({"staging", "main", "master", "production", "prod"})


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    code: str
    message: str
    escalate: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "code": self.code,
            "message": self.message,
            "escalate": self.escalate,
        }


def refuse_protected_branch_push(
    *,
    branch: Optional[str] = None,
    action: Optional[str] = None,
    proposal: Optional[Mapping[str, Any]] = None,
) -> PolicyDecision:
    """Refuse any proposal that would push directly to staging/main."""
    proposal = proposal or {}
    action = (action or str(proposal.get("action") or "")).strip().lower()
    branch = (branch or str(proposal.get("target_branch") or proposal.get("branch") or "")).strip()
    branch_l = branch.lower()

    if action in {
        "push_staging",
        "push_main",
        "direct_staging_push",
        "direct_main_push",
    }:
        return PolicyDecision(
            allowed=False,
            code="policy_refuse_protected_push",
            message=f"Refused forbidden action '{action}': no direct staging/main push",
            escalate=True,
        )
    if branch_l in PROTECTED_BRANCHES and action in {
        "push",
        "force_push",
        "direct_push",
        "publish_branch",
    }:
        return PolicyDecision(
            allowed=False,
            code="policy_refuse_protected_push",
            message=f"Refused push to protected branch '{branch}'",
            escalate=True,
        )
    if proposal.get("push_to_staging") or proposal.get("push_to_main"):
        return PolicyDecision(
            allowed=False,
            code="policy_refuse_protected_push",
            message="Refused proposal flags push_to_staging/push_to_main",
            escalate=True,
        )
    return PolicyDecision(allowed=True, code="ok", message="branch policy ok")


def refuse_permission_grant(proposal: Mapping[str, Any]) -> PolicyDecision:
    action = str(proposal.get("action") or "").strip().lower()
    if action in {"grant_permission", "grant_program_permission"} or proposal.get(
        "grant_permissions"
    ):
        return PolicyDecision(
            allowed=False,
            code="policy_refuse_permission_grant",
            message="Librarian must not grant Program permissions",
            escalate=True,
        )
    return PolicyDecision(allowed=True, code="ok", message="permission policy ok")


def escalate_low_confidence_merge_split(
    *,
    kind: str,
    confidence: Optional[float],
    threshold: float = 0.75,
) -> PolicyDecision:
    kind_l = kind.strip().lower()
    if kind_l not in {"merge", "split", "consolidation"}:
        return PolicyDecision(allowed=True, code="ok", message="not a merge/split")
    if confidence is None or confidence < threshold:
        return PolicyDecision(
            allowed=False,
            code="policy_escalate_low_confidence",
            message=(
                f"Low-confidence {kind_l} "
                f"(confidence={confidence}, threshold={threshold}) requires Principal review"
            ),
            escalate=True,
        )
    return PolicyDecision(allowed=True, code="ok", message="confidence acceptable")


def evaluate_proposal(proposal: Mapping[str, Any]) -> List[PolicyDecision]:
    """Run the full autonomy boundary suite against a proposal dict."""
    decisions = [
        refuse_protected_branch_push(proposal=proposal, action=proposal.get("action")),
        refuse_permission_grant(proposal),
    ]
    if str(proposal.get("kind") or proposal.get("action") or "").lower() in {
        "merge",
        "split",
        "propose_consolidation",
        "consolidation",
    }:
        decisions.append(
            escalate_low_confidence_merge_split(
                kind=str(proposal.get("kind") or proposal.get("action") or "consolidation"),
                confidence=(
                    float(proposal["confidence"])
                    if proposal.get("confidence") is not None
                    else None
                ),
            )
        )
    action = str(proposal.get("action") or "")
    if action in FORBIDDEN_ACTIONS:
        decisions.append(
            PolicyDecision(
                allowed=False,
                code="policy_forbidden_action",
                message=f"Forbidden action: {action}",
                escalate=True,
            )
        )
    return decisions


def first_blocking(decisions: Sequence[PolicyDecision]) -> Optional[PolicyDecision]:
    for decision in decisions:
        if not decision.allowed:
            return decision
    return None
