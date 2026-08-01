"""LiNKskills Eval Runner — observed-execution certification (Phase 3)."""

from .certify import CertificationDecision, certify_run
from .models import CaseResult, CaseStatus, EvalCase, EvalSuite, EvidenceArtifact, SuiteResult
from .runner import load_eval_suite, run_suite

# Backward-compatible alias.
RunResult = SuiteResult

__all__ = [
    "CaseResult",
    "CaseStatus",
    "CertificationDecision",
    "EvalCase",
    "EvalSuite",
    "EvidenceArtifact",
    "RunResult",
    "SuiteResult",
    "certify_run",
    "load_eval_suite",
    "run_suite",
]

__version__ = "0.1.0"
