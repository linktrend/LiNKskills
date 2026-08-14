"""Policy-only hostile-candidate sandbox planner; it never executes candidates."""
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass

FORBIDDEN = {"network", "subprocess", "secret_env", "symlink", "archive", "executable", "path_escape"}

@dataclass(frozen=True)
class SandboxPlan:
    candidate_digest: str; workspace_id: str; network: str = "deny"; cpu_seconds: int = 30; memory_mb: int = 256; output_bytes: int = 65536
    def evidence(self, evaluator: str, environment: str, policy: str) -> dict[str, str]:
        return {"candidate_digest": self.candidate_digest, "evaluator_release": evaluator, "environment_profile": environment, "policy_version": policy, "workspace_id": self.workspace_id}

def plan_candidate(candidate: dict) -> SandboxPlan:
    actions = set(candidate.get("declared_actions", []))
    if actions & FORBIDDEN: raise ValueError("quarantine:forbidden_candidate_capability")
    for path in candidate.get("paths", []):
        if not isinstance(path, str) or path.startswith("/") or ".." in path.split("/") or "\\" in path: raise ValueError("quarantine:unsafe_path")
    digest = "sha256:" + hashlib.sha256(json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return SandboxPlan(digest, "eval-" + digest[7:23])

def qualification_outcome(signal: str) -> str:
    return "hold_quarantine" if signal in {"timeout", "crash", "escape", "cleanup_failure", "policy_denied"} else "evidence_pending_review"
