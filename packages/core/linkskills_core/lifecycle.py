"""Certification lifecycle states and allowed transitions."""

from __future__ import annotations

from typing import Final, Literal

CertificationState = Literal["draft", "eval_pending", "usable", "deprecated", "retired"]

CERTIFICATION_STATES: Final[tuple[CertificationState, ...]] = (
    "draft",
    "eval_pending",
    "usable",
    "deprecated",
    "retired",
)

_ALLOWED: dict[CertificationState, frozenset[CertificationState]] = {
    "draft": frozenset({"eval_pending", "retired"}),
    "eval_pending": frozenset({"usable", "draft", "retired"}),
    "usable": frozenset({"deprecated", "retired"}),
    "deprecated": frozenset({"usable", "retired"}),
    "retired": frozenset(),
}


class TransitionError(ValueError):
    """Raised when a lifecycle transition is not allowed."""


def allowed_transitions(state: CertificationState) -> frozenset[CertificationState]:
    if state not in _ALLOWED:
        raise TransitionError(f"unknown lifecycle state: {state!r}")
    return _ALLOWED[state]


def can_transition(current: CertificationState, target: CertificationState) -> bool:
    if current not in _ALLOWED or target not in CERTIFICATION_STATES:
        return False
    return target in _ALLOWED[current]


def assert_transition(current: CertificationState, target: CertificationState) -> None:
    if not can_transition(current, target):
        raise TransitionError(f"transition not allowed: {current} -> {target}")
