#!/usr/bin/env python3
"""Batch-certify catalog skills through the Eval Runner pipeline.

Policy (ADR 0006 / 0009 + CLASSIFICATION-HONESTY):
- Production-facing ``skills_run_start`` requires ``certification_state=usable``.
- Filesystem presence alone never promotes.
- Only sealed executor receipts with ``network_isolation=denied`` can certify.
- Skills that do not satisfy the standard remain ``draft`` with machine-readable
  reasons in the report + classification ledger.

Reproducible sealed host command (local Docker Linux + bwrap, not stage/cloud):

  ./scripts/run-sealed-linux-certify.sh

This script never writes to Supabase / stage / VPS.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
for pkg in (
    "packages/contracts",
    "packages/core",
    "packages/publisher",
    "packages/eval_runner",
    "packages/tool_runtime",
    "packages/gateway",
    "packages/mcp_server",
    "packages/client",
    "packages/librarian_domain",
):
    sys.path.insert(0, str(REPO_ROOT / pkg))

from lib.skill_runtime.catalog import discover_skill_dirs  # noqa: E402
from lib.skill_runtime.certification_overlay import (  # noqa: E402
    classification_ledger_path,
    load_classification_ledger,
)

REPORT_REL = Path("evidence/phase10/catalog-certification-report.json")
SEALED_DIR_REL = Path("evidence/phase10/sealed")
CANARY_TOOL_ID = "text-echo"
CANARY_TOOL_VERSION = "1.0.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _proven_isolation_available() -> bool:
    try:
        from linkskills_tool_runtime.confined_exec import run_confined

        # Probe with a trivial argv under the workspace; fail closed on error.
        import tempfile

        with tempfile.TemporaryDirectory(prefix="linkskills-iso-") as tmp:
            result = run_confined(
                [sys.executable, "-c", "print('iso-ok')"],
                workspace=tmp,
                timeout_seconds=10,
            )
        return result.network_isolation == "denied"
    except Exception:
        return False


def build_canary_toolchain(repo_root: Path) -> Dict[str, Any]:
    """Bind observed text-echo descriptor/code hashes into the certification toolchain.

    ADR 0006 requires exact toolchain hashes so same-version code drift invalidates
    the execution profile. ``source_hash`` is the packaged tool tree hash from
    ``load_tool_descriptor`` / ``resolve_tool``; ``tool_hash`` aliases the binding
    hash used by the executor (bundle_hash when present, else source_hash).
    """
    from linkskills_tool_runtime.resolve import resolve_tool

    tool_dir = Path(repo_root) / "tools" / CANARY_TOOL_ID
    resolved = resolve_tool(
        tool_dir,
        tool_id=CANARY_TOOL_ID,
        version=CANARY_TOOL_VERSION,
    )
    source_hash = resolved.descriptor.source_hash
    if not source_hash:
        raise RuntimeError(
            f"{CANARY_TOOL_ID} descriptor missing source_hash after resolve "
            f"(path={tool_dir})"
        )
    tool_hash = resolved.bundle_hash or source_hash
    return {
        "tools": [
            {
                "tool_id": resolved.tool_id,
                "version": resolved.version,
                "source_hash": str(source_hash),
                "tool_hash": str(tool_hash),
            }
        ]
    }


def certification_exit_code(
    report: Dict[str, Any],
    *,
    requested_skills: Sequence[str],
    require_sealed: bool,
) -> int:
    """Exit policy for sealed catalog certification.

    - Explicit ``--skill`` list + sealed: nonzero if any requested skill is not usable.
    - Full-catalog sealed run: nonzero when usable_count == 0 (intended canary path
      failed / no canary became usable). Other skills remaining draft for
      suite_not_executable do not alone cause failure when usable_count > 0.
    - Unsealed / allow-unproven host: exit 0 (report still written).
    """
    if not require_sealed:
        return 0
    results = list(report.get("results") or [])
    if requested_skills:
        by_id = {str(r.get("skill_id")): r for r in results}
        for skill_id in requested_skills:
            item = by_id.get(str(skill_id))
            if item is None or item.get("classification") != "usable":
                return 1
        return 0
    if int(report.get("usable_count") or 0) == 0:
        return 1
    return 0


def _suite_path_for_skill(skill_dir: Path) -> Path:
    return skill_dir / "references" / "eval-suite.yaml"


def _evaluate_skill(
    skill_dir: Path,
    *,
    repo_root: Path,
    require_sealed: bool,
    isolation_ok: bool,
    toolchain: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return machine-readable certification outcome for one skill."""
    skill_id = skill_dir.name
    suite_path = _suite_path_for_skill(skill_dir)
    base: Dict[str, Any] = {
        "skill_id": skill_id,
        "skill_dir": str(skill_dir.relative_to(repo_root)),
        "suite_path": str(suite_path.relative_to(repo_root)) if suite_path.is_file() else None,
        "classification": "draft",
        "reason_code": "unknown",
        "reason": "",
        "certified": False,
        "evidence_path": None,
        "receipt_hashes": [],
        "skill_release_hash": None,
        "profile_hash": None,
        "toolchain": None,
        "source_hash": None,
        "tool_hash": None,
    }
    if not suite_path.is_file():
        base["reason_code"] = "missing_eval_suite"
        base["reason"] = "references/eval-suite.yaml missing"
        return base

    from linkskills_eval_runner.certify import certify_run
    from linkskills_eval_runner.executor import compute_skill_release_hash
    from linkskills_eval_runner.judge import IndependentDeterministicJudge
    from linkskills_eval_runner.runner import load_eval_suite, run_suite

    try:
        suite = load_eval_suite(suite_path)
    except Exception as exc:  # noqa: BLE001 — report as draft reason
        base["reason_code"] = "suite_load_error"
        base["reason"] = f"failed to load eval suite: {exc}"
        return base

    executable = [c for c in suite.cases if c.is_executable]
    if not executable:
        base["reason_code"] = "suite_not_executable"
        base["reason"] = (
            "eval suite has no execute blocks; prompt-only / judged-shape suites "
            "cannot certify (ADR 0006)"
        )
        return base
    if any(c.suite_authored_output for c in suite.cases):
        base["reason_code"] = "suite_authored_output_present"
        base["reason"] = "suite-authored observed/fixture output cannot authorize certification"
        return base

    if require_sealed and not isolation_ok:
        base["reason_code"] = "isolation_unavailable"
        base["reason"] = (
            "host cannot stamp network_isolation=denied; run "
            "./scripts/run-sealed-linux-certify.sh (Linux bwrap / privileged Docker)"
        )
        return base

    bound_toolchain = toolchain if toolchain is not None else build_canary_toolchain(repo_root)
    tool0 = (bound_toolchain.get("tools") or [{}])[0]
    base["toolchain"] = bound_toolchain
    base["source_hash"] = tool0.get("source_hash")
    base["tool_hash"] = tool0.get("tool_hash")

    release_hash = compute_skill_release_hash(skill_dir)
    judge = IndependentDeterministicJudge()
    result = run_suite(
        suite,
        judge=judge,
        toolchain=bound_toolchain,
        repo_root=repo_root,
        skill_dir=skill_dir,
        skill_release_hash=release_hash,
    )
    decision = certify_run(
        result,
        judge=judge,
        rubric=suite.rubric,
        pass_threshold=suite.pass_threshold,
        expected_skill_release_hash=release_hash,
    )
    base["skill_release_hash"] = decision.skill_release_hash or release_hash
    base["profile_hash"] = decision.profile_hash
    base["receipt_hashes"] = list(decision.receipt_hashes or [])
    base["weighted_score"] = decision.weighted_score
    base["certify_reason"] = decision.reason
    base["passed"] = result.passed

    isolations = {
        (c.execution_receipt or {}).get("network_isolation")
        for c in result.case_results
        if c.execution_receipt
    }
    if require_sealed and isolations != {"denied"}:
        base["reason_code"] = "receipt_isolation_not_denied"
        base["reason"] = (
            f"execution receipts isolation={sorted(isolations)!r}; "
            "certification requires network_isolation=denied"
        )
        return base

    if not decision.certified:
        base["reason_code"] = "certify_refused"
        base["reason"] = decision.reason
        return base

    evidence_rel = SEALED_DIR_REL / f"{skill_id}-sealed.json"
    evidence_path = repo_root / evidence_rel
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "skill_id": skill_id,
        "certified": True,
        "certify_reason": decision.reason,
        "skill_release_hash": base["skill_release_hash"],
        "profile_hash": decision.profile_hash,
        "receipt_hashes": decision.receipt_hashes,
        "suite_hash": result.suite_hash,
        "weighted_score": decision.weighted_score,
        "network_isolation": "denied",
        "toolchain": bound_toolchain,
        "source_hash": base["source_hash"],
        "tool_hash": base["tool_hash"],
        "host": {
            "platform": sys.platform,
            "issuer_id": os.environ.get("LINKSKILLS_EVAL_RUNNER_ISSUER_ID", ""),
            "sealed_path": "linux-bwrap-or-approved-container",
        },
        "generated_at": _utc_now(),
        "execution_receipts": result.execution_receipts,
        "cases": [
            {
                "case_id": c.case_id,
                "status": c.status.value,
                "evidence_source": c.evidence_source,
                "execution_receipt": c.execution_receipt,
            }
            for c in result.case_results
        ],
    }
    evidence_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    base["classification"] = "usable"
    base["certified"] = True
    base["reason_code"] = "certified_usable"
    base["reason"] = decision.reason
    base["evidence_path"] = str(evidence_rel)
    return base


def _update_ledger(
    repo_root: Path,
    results: Sequence[Dict[str, Any]],
    *,
    isolation_ok: bool,
) -> Dict[str, Any]:
    path = classification_ledger_path(repo_root)
    ledger = load_classification_ledger(repo_root)
    if not ledger:
        ledger = {
            "note": "Honest classification ledger generated by scripts/certify-catalog.py",
            "skills": {},
            "counts": {},
        }
    skills = dict(ledger.get("skills") or {})
    sealed_paths: List[str] = []
    for item in results:
        skill_id = item["skill_id"]
        prior = dict(skills.get(skill_id) or {})
        evidence: List[str] = []
        if item.get("evidence_path"):
            evidence = [str(item["evidence_path"])]
            sealed_paths.append(str(item["evidence_path"]))
        prior.update(
            {
                "classification": item["classification"],
                "sealed_live_receipt_evidence": evidence,
                "reason": item["reason"],
                "reason_code": item["reason_code"],
                "suite_executable": item["reason_code"]
                not in {"suite_not_executable", "missing_eval_suite", "suite_load_error"},
            }
        )
        if item.get("skill_release_hash"):
            prior["skill_release_hash"] = item["skill_release_hash"]
        if item.get("profile_hash"):
            prior["profile_hash"] = item["profile_hash"]
        if item.get("source_hash"):
            prior["source_hash"] = item["source_hash"]
        if item.get("tool_hash"):
            prior["tool_hash"] = item["tool_hash"]
        if item.get("toolchain"):
            prior["toolchain"] = item["toolchain"]
        skills[skill_id] = prior

    counts = {
        "total_catalog_skills": len(skills),
        "draft": sum(1 for s in skills.values() if s.get("classification") == "draft"),
        "usable": sum(1 for s in skills.values() if s.get("classification") == "usable"),
        "eval_pending": sum(
            1 for s in skills.values() if s.get("classification") == "eval_pending"
        ),
        "deprecated": sum(
            1 for s in skills.values() if s.get("classification") == "deprecated"
        ),
        "retired": sum(1 for s in skills.values() if s.get("classification") == "retired"),
        "with_sealed_live_receipts": sum(
            1
            for s in skills.values()
            if isinstance(s.get("sealed_live_receipt_evidence"), list)
            and s.get("sealed_live_receipt_evidence")
        ),
    }
    ledger["skills"] = dict(sorted(skills.items()))
    ledger["counts"] = counts
    ledger["updated_at"] = _utc_now()
    ledger["as_of"] = ledger["updated_at"][:10]
    ledger["macos_certifiable"] = False
    ledger["linux_bwrap_required"] = True
    ledger["sealed_live_receipt_evidence_paths"] = sealed_paths
    if counts["usable"] > 0 and isolation_ok:
        ledger["live_certification"] = (
            f"local sealed Linux/container certification performed {_utc_now()} "
            f"({counts['usable']} usable)"
        )
        ledger["evidence_tier"] = (
            "sealed local Linux bwrap (or privileged Docker Linux); not stage/prod apply"
        )
    else:
        ledger["live_certification"] = ledger.get("live_certification") or "not performed"
    path.write_text(json.dumps(ledger, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return ledger


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--skill",
        action="append",
        default=[],
        help="Limit to one or more skill ids (default: all catalog skills)",
    )
    parser.add_argument(
        "--require-sealed",
        action="store_true",
        default=True,
        help="Require network_isolation=denied (default)",
    )
    parser.add_argument(
        "--allow-unproven-host",
        action="store_true",
        help="Attempt runs even when isolation probe fails (still will not promote unproven)",
    )
    parser.add_argument(
        "--write-ledger",
        action="store_true",
        default=True,
        help="Update evidence/phase10/skill-classification-draft.json (default)",
    )
    parser.add_argument(
        "--no-write-ledger",
        action="store_true",
        help="Do not mutate the classification ledger",
    )
    parser.add_argument(
        "--rebuild-catalog",
        action="store_true",
        default=True,
        help="Rebuild catalog/index.json from ledger overlay (default)",
    )
    parser.add_argument(
        "--no-rebuild-catalog",
        action="store_true",
        help="Skip catalog rebuild",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    repo_root = args.repo_root.resolve()
    require_sealed = bool(args.require_sealed) and not args.allow_unproven_host
    isolation_ok = _proven_isolation_available()

    skill_dirs = discover_skill_dirs(repo_root)
    if args.skill:
        wanted = set(args.skill)
        skill_dirs = [d for d in skill_dirs if d.name in wanted]
        missing = wanted - {d.name for d in skill_dirs}
        if missing:
            print(f"unknown skill id(s): {sorted(missing)}", file=sys.stderr)
            return 2

    # Resolve once so profile_hash binds the observed packaged tool hash for all
    # executable suites in this run (canary path). Non-executable skills never reach
    # run_suite and ignore toolchain.
    toolchain: Optional[Dict[str, Any]] = None
    try:
        toolchain = build_canary_toolchain(repo_root)
    except Exception as exc:  # noqa: BLE001 — report per-skill if needed later
        print(f"warning: canary toolchain resolve failed: {exc}", file=sys.stderr)

    results = [
        _evaluate_skill(
            skill_dir,
            repo_root=repo_root,
            require_sealed=require_sealed,
            isolation_ok=isolation_ok,
            toolchain=toolchain,
        )
        for skill_dir in skill_dirs
    ]

    report = {
        "generated_at": _utc_now(),
        "repo_root_marker": "LiNKskills",
        "isolation_probe_denied": isolation_ok,
        "require_sealed": require_sealed,
        "platform": sys.platform,
        "toolchain": toolchain,
        "skill_count": len(results),
        "usable_count": sum(1 for r in results if r["classification"] == "usable"),
        "draft_count": sum(1 for r in results if r["classification"] == "draft"),
        "results": results,
    }
    report_path = repo_root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Wrote {report_path.relative_to(repo_root)} "
        f"(usable={report['usable_count']} draft={report['draft_count']} "
        f"isolation_denied={isolation_ok})"
    )

    if args.write_ledger and not args.no_write_ledger:
        ledger = _update_ledger(repo_root, results, isolation_ok=isolation_ok)
        print(
            f"Updated {classification_ledger_path(repo_root).relative_to(repo_root)} "
            f"counts={ledger.get('counts')}"
        )

    if args.rebuild_catalog and not args.no_rebuild_catalog:
        import subprocess

        from lib.skill_runtime.catalog import build_catalog_index, write_catalog_index
        from lib.skill_runtime.certification_overlay import (
            load_certification_overlay,
            load_hash_overlay,
        )

        # Prefer explicit pin (sealed Docker host → container) over in-container git.
        git_sha = os.environ.get("LINKSKILLS_CATALOG_GIT_SHA", "").strip() or None
        if not git_sha:
            try:
                git_sha = (
                    subprocess.check_output(
                        ["git", "rev-parse", "HEAD"],
                        cwd=repo_root,
                        stderr=subprocess.DEVNULL,
                        text=True,
                    ).strip()
                    or None
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                git_sha = None
        overlay = load_certification_overlay(repo_root)
        hashes = load_hash_overlay(repo_root)
        index = build_catalog_index(
            repo_root,
            certification_overlay=overlay,
            hash_overlay=hashes,
            git_sha=git_sha,
        )
        written = write_catalog_index(repo_root, index)
        usable = sum(
            1 for s in index["skills"] if s.get("certification_state") == "usable"
        )
        print(
            f"Wrote {written.relative_to(repo_root)} "
            f"(usable={usable}/{index['skill_count']})"
        )

    return certification_exit_code(
        report,
        requested_skills=list(args.skill or []),
        require_sealed=require_sealed,
    )


if __name__ == "__main__":
    raise SystemExit(main())
