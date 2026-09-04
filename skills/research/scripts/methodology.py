#!/usr/bin/env python3
"""Acyclic research methodology aligned to protected LR-WP-002 vocabulary.

This module is a LiNKskills consumer of frozen LiNKresearch domain terms. It
does not copy Harness/LiNKresearch packages, grant Brain authority, or call a
provider. Closed enumerations are pinned in
``skills/research/references/lr-wp-002-vocabulary.json``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


VOCABULARY_PATH = (
    Path(__file__).resolve().parents[1] / "references" / "lr-wp-002-vocabulary.json"
)

WORKSTREAM_RANK = {
    "collect": 1,
    "extract": 2,
    "claim": 3,
    "verify": 4,
    "synthesize": 5,
    "refresh": 6,
}

CLAIM_LINK_RELS = frozenset({"supports", "contradicts", "qualifies", "cites"})
CLAIM_LINK_TARGET_KINDS = frozenset({"source-version", "evidence-excerpt", "claim"})
INTAKE_KINDS = frozenset({"question", "hypothesis", "comparison", "audit", "refresh"})
SOURCE_KINDS = frozenset({"document", "url", "interview", "dataset", "api", "notebook"})
NEGATIVE_EVIDENCE_CLASSES = frozenset({"missing", "observed_absence"})

LEGACY_ROUTER_MARKERS = (
    "/tools/research",
    "tools/research/bin/research",
    "tools/research/",
)

NAMED_PROVIDER_PATTERNS = (
    re.compile(r"\bexa\b", re.I),
    re.compile(r"\btavily\b", re.I),
    re.compile(r"\bserper\b", re.I),
    re.compile(r"\bperplexity\b", re.I),
    re.compile(r"\bbrave search\b", re.I),
    re.compile(r"\bbing api\b", re.I),
    re.compile(r"google custom search", re.I),
    re.compile(r"\bkagi\b", re.I),
)


def load_accepted_vocabulary(path: Path | None = None) -> dict[str, Any]:
    """Return the pinned LR-WP-002 closed vocabulary consumed by this skill family."""

    payload = json.loads((path or VOCABULARY_PATH).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("vocabulary must be a JSON object")
    return payload


def assert_vocabulary_pin(payload: Mapping[str, Any] | None = None) -> list[str]:
    """Return errors when the consumer pin does not match protected LR-WP-002 enums."""

    vocab = dict(payload) if payload is not None else load_accepted_vocabulary()
    errors: list[str] = []
    if vocab.get("packet") != "LR-WP-002":
        errors.append("vocabulary packet must be LR-WP-002")
    if vocab.get("schemaFamily") != "linkresearch.domain":
        errors.append("vocabulary schemaFamily must be linkresearch.domain")
    if vocab.get("domainVersion") != "1.0.0":
        errors.append("vocabulary domainVersion must be 1.0.0")
    if vocab.get("frozen") is not True:
        errors.append("vocabulary must be frozen")
    enums = vocab.get("enums") if isinstance(vocab.get("enums"), dict) else {}
    expected = {
        "intakeKind": sorted(INTAKE_KINDS),
        "workstreamKind": sorted(WORKSTREAM_RANK),
        "claimLinkRel": sorted(CLAIM_LINK_RELS),
        "claimLinkTargetKind": sorted(CLAIM_LINK_TARGET_KINDS),
        "sourceKind": sorted(SOURCE_KINDS),
    }
    for key, values in expected.items():
        observed = enums.get(key)
        if not isinstance(observed, list) or sorted(str(item) for item in observed) != values:
            errors.append(f"vocabulary enum {key} does not match accepted LR-WP-002 set")
    return errors


def workstream_errors(workstreams: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return errors when workstreams are empty, colliding, or cyclic in kind order."""

    errors: list[str] = []
    if not workstreams:
        errors.append("workstreams must contain at least one step")
        return errors
    sequences: list[int] = []
    ranked: list[tuple[int, int, str]] = []
    for index, row in enumerate(workstreams):
        kind = str(row.get("kind") or "")
        if kind not in WORKSTREAM_RANK:
            errors.append(f"workstream[{index}] has unknown kind {kind!r}")
            continue
        try:
            sequence = int(row.get("sequence"))
        except (TypeError, ValueError):
            errors.append(f"workstream[{index}] sequence must be an integer")
            continue
        if sequence < 1:
            errors.append(f"workstream[{index}] sequence must be >= 1")
            continue
        sequences.append(sequence)
        ranked.append((sequence, index, kind))
    if len(sequences) != len(set(sequences)):
        errors.append("workstream sequence must be unique")
    previous_rank = 0
    for _sequence, _index, kind in sorted(ranked, key=lambda item: item[0]):
        rank = WORKSTREAM_RANK[kind]
        if rank < previous_rank:
            errors.append(
                f"workstream kind {kind!r} regresses methodology order and would form a cycle"
            )
        previous_rank = rank
    return errors


def _has_cycle(edges: Sequence[tuple[str, str]]) -> bool:
    adjacency: dict[str, list[str]] = {}
    nodes: set[str] = set()
    for source, target in edges:
        adjacency.setdefault(source, []).append(target)
        nodes.add(source)
        nodes.add(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for nxt in adjacency.get(node, []):
            if visit(nxt):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in nodes)


def claim_graph_errors(
    claims: Sequence[Mapping[str, Any]],
    links: Sequence[Mapping[str, Any]],
) -> list[str]:
    """Return errors for self-supersession, self-links, unknown targets, or cycles."""

    errors: list[str] = []
    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        claim_id = str(claim.get("claim_id") or claim.get("id") or "")
        if not claim_id:
            errors.append(f"claim[{index}] missing claim_id")
            continue
        if claim_id in claim_ids:
            errors.append(f"duplicate claim_id {claim_id!r}")
        claim_ids.add(claim_id)
    for claim in claims:
        claim_id = str(claim.get("claim_id") or claim.get("id") or "")
        supersedes = claim.get("supersedes_claim_id") or claim.get("supersedesClaimId")
        if not supersedes:
            continue
        if str(supersedes) == claim_id:
            errors.append("claim cannot supersede itself")
        elif str(supersedes) not in claim_ids:
            errors.append(f"supersedes_claim_id {supersedes!r} is not in-graph")
    edges: list[tuple[str, str]] = []
    for index, link in enumerate(links):
        rel = str(link.get("rel") or "")
        if rel not in CLAIM_LINK_RELS:
            errors.append(f"claim_link[{index}] rel must be one of {sorted(CLAIM_LINK_RELS)}")
        target_kind = str(link.get("target_kind") or link.get("targetKind") or "")
        if target_kind not in CLAIM_LINK_TARGET_KINDS:
            errors.append(f"claim_link[{index}] target_kind is not an accepted LR-WP-002 kind")
        claim_id = str(link.get("claim_id") or link.get("claimId") or "")
        target_id = str(link.get("target_id") or link.get("targetId") or "")
        if claim_id not in claim_ids:
            errors.append(f"claim_link[{index}] missing claim {claim_id!r}")
        if target_kind == "claim":
            if target_id == claim_id:
                errors.append("claim cannot link to itself")
            if target_id not in claim_ids:
                errors.append(f"claim_link[{index}] missing target claim {target_id!r}")
            else:
                edges.append((claim_id, target_id))
    if _has_cycle(edges):
        errors.append("claim-to-claim links must be acyclic")
    return errors


def conflict_set_errors(
    claims: Sequence[Mapping[str, Any]],
    conflict_sets: Sequence[Mapping[str, Any]],
) -> list[str]:
    """Return errors when a conflict set has fewer than two distinct in-graph claims."""

    claim_ids = {
        str(claim.get("claim_id") or claim.get("id") or "")
        for claim in claims
        if claim.get("claim_id") or claim.get("id")
    }
    errors: list[str] = []
    for index, row in enumerate(conflict_sets):
        raw_ids = row.get("claim_ids") or row.get("claimIds") or []
        if not isinstance(raw_ids, list):
            errors.append(f"conflict_set[{index}] claim_ids must be an array")
            continue
        ids = [str(item) for item in raw_ids]
        if len(set(ids)) != len(ids):
            errors.append(f"conflict_set[{index}] claim_ids must be unique")
        if len(set(ids)) < 2:
            errors.append("conflict set must contain at least two distinct claims")
        for claim_id in ids:
            if claim_id not in claim_ids:
                errors.append(f"conflict_set[{index}] missing claim {claim_id!r}")
    return errors


def classify_negative_evidence(record: Mapping[str, Any]) -> dict[str, Any]:
    """Distinguish missing evidence from observed absence (negative evidence)."""

    evidence_class = str(record.get("evidence_class") or record.get("class") or "")
    pointers = record.get("source_pointers") or record.get("sourcePointers") or []
    rel = str(record.get("rel") or "")
    if evidence_class == "observed_absence" or rel == "contradicts":
        if isinstance(pointers, list) and pointers:
            return {
                "class": "observed_absence",
                "finalization": "allowed_if_cited",
                "note": "Evidence of absence requires a concrete source pointer and contradicts rel.",
            }
        return {
            "class": "missing",
            "finalization": "blocked",
            "note": "Absence was asserted without a source pointer.",
        }
    if not isinstance(pointers, list) or not pointers:
        return {
            "class": "missing",
            "finalization": "blocked",
            "note": "Missing evidence is not evidence of absence.",
        }
    return {
        "class": "observed_presence",
        "finalization": "allowed_if_cited",
        "note": "Presence evidence is cited.",
    }


def provider_neutrality_errors(text: str) -> list[str]:
    """Return errors when a named retrieval provider or vendor endpoint is required."""

    errors = [
        f"named retrieval provider is forbidden: {pattern.pattern}"
        for pattern in NAMED_PROVIDER_PATTERNS
        if pattern.search(text)
    ]
    return errors


def legacy_router_errors(text: str) -> list[str]:
    """Return errors when the excluded ``tools/research`` router is selected."""

    lowered = text.lower()
    errors: list[str] = []
    for marker in LEGACY_ROUTER_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"legacy research router is excluded: {marker}")
    return errors


def skill_dependency_cycle_errors(graph: Mapping[str, Iterable[str]]) -> list[str]:
    """Return errors when skill dependencies among the methodology family cycle."""

    edges: list[tuple[str, str]] = []
    for source, targets in graph.items():
        for target in targets:
            edges.append((str(source), str(target)))
    if _has_cycle(edges):
        return ["research methodology skill dependencies must be acyclic"]
    return []


def facade_outcome(requested_skill: str, *, new_broad_workflow: bool) -> dict[str, Any]:
    """Return the one-way search-strategy facade or supersession outcome."""

    requested = requested_skill.strip()
    if requested == "search-strategy" and new_broad_workflow:
        return {
            "selected_skill": "research",
            "requested_skill": "search-strategy",
            "outcome": "supersession",
            "direction": "one-way",
            "legacy_skill_rewritten": False,
            "citation_enforcer": "independently_composable",
        }
    if requested == "search-strategy":
        return {
            "selected_skill": "research",
            "requested_skill": "search-strategy",
            "outcome": "facade",
            "direction": "one-way",
            "legacy_skill_rewritten": False,
            "citation_enforcer": "independently_composable",
        }
    return {
        "selected_skill": requested or "research",
        "requested_skill": requested,
        "outcome": "direct",
        "direction": "one-way",
        "legacy_skill_rewritten": False,
        "citation_enforcer": "independently_composable",
    }


def evaluate_methodology(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a redacted methodology record and return an effect-free report."""

    errors: list[str] = []
    errors.extend(assert_vocabulary_pin())
    workstreams = payload.get("workstreams") or []
    claims = payload.get("claims") or []
    links = payload.get("claim_links") or payload.get("claimLinks") or []
    conflicts = payload.get("conflict_sets") or payload.get("conflictSets") or []
    if not isinstance(workstreams, list):
        errors.append("workstreams must be an array")
        workstreams = []
    if not isinstance(claims, list):
        errors.append("claims must be an array")
        claims = []
    if not isinstance(links, list):
        errors.append("claim_links must be an array")
        links = []
    if not isinstance(conflicts, list):
        errors.append("conflict_sets must be an array")
        conflicts = []
    errors.extend(workstream_errors(workstreams))
    errors.extend(claim_graph_errors(claims, links))
    errors.extend(conflict_set_errors(claims, conflicts))
    intake_kind = str(payload.get("intake_kind") or payload.get("kind") or "")
    if intake_kind and intake_kind not in INTAKE_KINDS:
        errors.append(f"intake_kind {intake_kind!r} is not an accepted LR-WP-002 kind")
    blob = json.dumps(payload, sort_keys=True)
    errors.extend(provider_neutrality_errors(blob))
    errors.extend(legacy_router_errors(blob))
    negative = [
        classify_negative_evidence(claim)
        for claim in claims
        if isinstance(claim, Mapping)
    ]
    if any(item["finalization"] == "blocked" for item in negative):
        errors.append("negative or missing evidence blocks finalization")
    return {
        "status": "FAILED" if errors else "SUCCESS",
        "errors": errors,
        "negative_evidence": negative,
        "external_calls": [],
        "mutations": [],
    }
