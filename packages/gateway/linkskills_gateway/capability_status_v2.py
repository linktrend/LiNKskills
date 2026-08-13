"""Truthful provider capability status; health is never consumer/E2E proof."""
from __future__ import annotations
from dataclasses import dataclass

STATES = {"available", "degraded", "offline", "unauthorized", "forbidden", "contract_incompatible", "stale", "disabled"}
CAPABILITIES = (
    "catalogue_index", "search_describe_fragments_resources", "exact_release_package",
    "integrity_validation", "qualification_evaluation", "telemetry_intake",
    "feedback_candidate_intake", "librarian_review_queue", "migration_compatibility",
)

@dataclass(frozen=True)
class CapabilityStatus:
    name: str; state: str; contract_version: str = "skills.api.v0.2"; detail: str = ""
    def __post_init__(self):
        if self.name not in CAPABILITIES or self.state not in STATES: raise ValueError("invalid_capability_status")
    def as_dict(self) -> dict[str, str]:
        return {"name":self.name,"state":self.state,"contract_version":self.contract_version,"detail":self.detail,"does_not_prove":"consumer_execution_or_production_readiness"}

def readiness(statuses: list[CapabilityStatus]) -> dict[str, object]:
    blocked = [s.name for s in statuses if s.state not in {"available", "degraded"}]
    return {"liveness":"process_only", "readiness":"ready" if not blocked else "not_ready", "blocked_capabilities":blocked, "does_not_prove":"release_qualification_consumer_execution_workflow_completion_or_production"}
