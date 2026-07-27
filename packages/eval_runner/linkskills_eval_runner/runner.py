"""Eval suite loader and deterministic case runner."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional, Union

from .assertions import (
    AssertionHardFail,
    assertions_hard_failed,
    assertions_passed,
    parse_assertion_spec,
    run_assertions,
)
from .executor import (
    case_has_execute_block,
    case_has_suite_authored_output,
    execute_case,
)
from .judge import IndependentDeterministicJudge, QualitativeJudge
from .models import (
    AssertionResult,
    CaseResult,
    CaseStatus,
    EvalCase,
    EvalSuite,
    EvidenceArtifact,
    RubricDimension,
    SuiteResult,
)
from .workspace import EvalWorkspace


class YamlDependencyError(RuntimeError):
    """Raised when YAML cannot be loaded."""


def _import_yaml():
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    return yaml


def _minimal_yaml_load(text: str) -> Any:
    """Load a constrained YAML subset used by Phase 3 canary fixtures.

    Supports mappings, lists, scalars, and block scalars (|) at shallow depth.
    Prefer PyYAML when installed; this exists only as a free fallback.
    """
    lines = text.splitlines()
    root: Any = None
    stack: list[tuple[int, Any]] = []

    def _parse_scalar(raw: str) -> Any:
        value = raw.strip()
        if value in {"", "~", "null", "Null", "NULL"}:
            return None
        if value in {"true", "True", "TRUE"}:
            return True
        if value in {"false", "False", "FALSE"}:
            return False
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]
        if re.fullmatch(r"-?\d+", value):
            return int(value)
        if re.fullmatch(r"-?\d+\.\d+", value):
            return float(value)
        return value

    def _current_container(indent: int) -> Any:
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            return None
        return stack[-1][1]

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            i += 1
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if line.startswith("- "):
            item_raw = line[2:].strip()
            container = _current_container(indent)
            if container is None:
                root = []
                stack.append((indent, root))
                container = root
            if not isinstance(container, list):
                raise YamlDependencyError("minimal YAML: list item under non-list")
            if item_raw.endswith(":") or (":" in item_raw and not item_raw.startswith("|")):
                # mapping entry inside list item: "- key: value" or "- key:"
                mapping: dict[str, Any] = {}
                container.append(mapping)
                stack.append((indent + 2, mapping))
                if item_raw.endswith(":"):
                    key = item_raw[:-1].strip()
                    # look ahead for nested block
                    mapping[key] = None
                    # leave value to be filled by nested structure; keep key pending via sentinel
                    # Re-parse as key with empty value by pushing a nested parse via synthetic line
                    # Simpler path: handle "- key: value" inline and "- key:" with nested body.
                    pass
                if ":" in item_raw:
                    key, _, rest = item_raw.partition(":")
                    key = key.strip()
                    rest = rest.strip()
                    if rest == "|":
                        block_lines: list[str] = []
                        i += 1
                        while i < len(lines):
                            nxt = lines[i]
                            if not nxt.strip():
                                block_lines.append("")
                                i += 1
                                continue
                            nxt_indent = len(nxt) - len(nxt.lstrip(" "))
                            if nxt_indent <= indent:
                                break
                            block_lines.append(nxt[indent + 2 :])
                            i += 1
                        mapping[key] = "\n".join(block_lines).rstrip("\n")
                        continue
                    if rest == "":
                        mapping[key] = None
                    else:
                        mapping[key] = _parse_scalar(rest)
                i += 1
                continue
            if item_raw == "|":
                block_lines = []
                i += 1
                while i < len(lines):
                    nxt = lines[i]
                    if not nxt.strip():
                        block_lines.append("")
                        i += 1
                        continue
                    nxt_indent = len(nxt) - len(nxt.lstrip(" "))
                    if nxt_indent <= indent:
                        break
                    block_lines.append(nxt[indent + 2 :])
                    i += 1
                container.append("\n".join(block_lines).rstrip("\n"))
                continue
            container.append(_parse_scalar(item_raw))
            i += 1
            continue

        if ":" in line:
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            container = _current_container(indent)
            if container is None:
                root = {}
                stack.append((indent, root))
                container = root
            if not isinstance(container, dict):
                raise YamlDependencyError("minimal YAML: mapping entry under non-mapping")
            if rest == "|":
                block_lines = []
                i += 1
                while i < len(lines):
                    nxt = lines[i]
                    if not nxt.strip():
                        block_lines.append("")
                        i += 1
                        continue
                    nxt_indent = len(nxt) - len(nxt.lstrip(" "))
                    if nxt_indent <= indent:
                        break
                    block_lines.append(nxt[indent + 2 :])
                    i += 1
                container[key] = "\n".join(block_lines).rstrip("\n")
                continue
            if rest == "":
                # Peek next non-empty line to decide list vs mapping.
                j = i + 1
                child: Any = {}
                while j < len(lines):
                    peek = lines[j]
                    if not peek.strip() or peek.lstrip().startswith("#"):
                        j += 1
                        continue
                    peek_indent = len(peek) - len(peek.lstrip(" "))
                    if peek_indent > indent and peek.strip().startswith("- "):
                        child = []
                    break
                container[key] = child
                stack.append((indent + 2 if indent == 0 else indent + 2, child))
                # Use consistent child indent of indent+2
                stack[-1] = (indent + 2, child)
            else:
                container[key] = _parse_scalar(rest)
            i += 1
            continue

        raise YamlDependencyError(f"minimal YAML: unsupported syntax near: {line!r}")

    if root is None:
        return {}
    return root


def load_yaml_text(text: str) -> Any:
    """Load YAML using PyYAML when available; otherwise a minimal subset parser."""
    yaml = _import_yaml()
    if yaml is not None:
        return yaml.safe_load(text)
    try:
        return _minimal_yaml_load(text)
    except Exception as exc:  # pragma: no cover - defensive
        raise YamlDependencyError(
            "PyYAML is required to load this eval-suite.yaml (minimal subset failed). "
            "Install the free package with: pip install PyYAML"
        ) from exc


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _as_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value)


def _parse_case(raw: dict[str, Any], suite_dir: Path) -> EvalCase:
    case_id = str(raw.get("id") or raw.get("case_id") or "unnamed")
    # Suite-authored observed_output / fixture_output are golden/expected only.
    golden: Optional[str] = None
    suite_authored = False
    if raw.get("observed_output") is not None:
        golden = _as_str(raw.get("observed_output"))
        suite_authored = True
    fixture_raw = raw.get("fixture_output")
    if fixture_raw is not None:
        suite_authored = True
        if isinstance(fixture_raw, str):
            candidate = (suite_dir / fixture_raw).resolve()
            if candidate.is_file():
                golden = candidate.read_text(encoding="utf-8")
            else:
                golden = fixture_raw
        else:
            golden = _as_str(fixture_raw)
    if raw.get("expected_output") is not None and golden is None:
        golden = _as_str(raw.get("expected_output"))

    criteria = raw.get("expected_criteria")
    if criteria is None:
        expected = raw.get("expected")
        if isinstance(expected, dict):
            criteria = expected.get("criteria") or []
        else:
            criteria = []
    if not isinstance(criteria, list):
        criteria = [str(criteria)]

    assertions_raw = raw.get("assertions")
    if assertions_raw is None:
        assertions_raw = raw.get("deterministic_assertions")

    try:
        assertions = parse_assertion_spec(assertions_raw)
    except AssertionHardFail:
        raise

    # If golden exact text is provided, surface it as exact_output when unset.
    if golden is not None and assertions.exact_output is None and raw.get("assert_exact_golden"):
        assertions.exact_output = golden

    has_execute = isinstance(raw.get("execute"), dict) and bool(
        (raw.get("execute") or {}).get("kind")
    )

    return EvalCase(
        id=case_id,
        input=str(raw.get("input") or ""),
        expected_criteria=[str(c) for c in criteria],
        assertions=assertions,
        golden_output=golden,
        suite_authored_output=suite_authored,
        has_execute=has_execute,
        raw=dict(raw),
    )


def load_eval_suite(path: Union[str, Path]) -> EvalSuite:
    """Load and normalize an eval-suite.yaml file."""
    suite_path = Path(path).resolve()
    if not suite_path.is_file():
        raise FileNotFoundError(f"eval suite not found: {suite_path}")

    text = suite_path.read_text(encoding="utf-8")
    data = load_yaml_text(text)
    if not isinstance(data, dict):
        raise ValueError(f"eval suite must be a mapping: {suite_path}")

    cases_raw = data.get("cases")
    if cases_raw is None:
        cases_raw = data.get("scenarios") or []
    if not isinstance(cases_raw, list):
        raise ValueError("eval suite cases/scenarios must be a list")

    suite_dir = suite_path.parent
    cases = [
        _parse_case(item, suite_dir)
        for item in cases_raw
        if isinstance(item, dict)
    ]

    rubric_raw = data.get("rubric") or []
    rubric: list[RubricDimension] = []
    if isinstance(rubric_raw, list):
        for item in rubric_raw:
            if not isinstance(item, dict):
                continue
            dim = item.get("dimension")
            if not dim:
                continue
            weight = float(item.get("weight") or 0.0)
            hard = item.get("hard_fail_below")
            rubric.append(
                RubricDimension(
                    dimension=str(dim),
                    weight=weight,
                    hard_fail_below=float(hard) if hard is not None else None,
                )
            )

    skill_id = str(data.get("skill_id") or suite_path.parent.parent.name)
    suite_id = str(data.get("suite_id") or f"{skill_id}-suite")
    suite_version = str(data.get("suite_version") or data.get("version") or "0.0.0")
    pass_threshold = float(data.get("pass_threshold") or 0.8)
    judge_config = data.get("judge") if isinstance(data.get("judge"), dict) else {}

    return EvalSuite(
        skill_id=skill_id,
        suite_id=suite_id,
        suite_version=suite_version,
        pass_threshold=pass_threshold,
        rubric=rubric,
        cases=cases,
        source_path=str(suite_path),
        suite_hash=_sha256_text(text),
        judge_config=judge_config,
        raw=data,
    )


def weighted_score(
    scores: dict[str, float],
    rubric: list[RubricDimension],
) -> tuple[float, list[str]]:
    """Return (weighted_score, hard_fail_dimensions)."""
    if not rubric:
        if not scores:
            return 0.0, []
        values = list(scores.values())
        return sum(values) / len(values), []

    total_weight = sum(d.weight for d in rubric) or 1.0
    acc = 0.0
    hard_dims: list[str] = []
    for dim in rubric:
        value = float(scores.get(dim.dimension, 0.0))
        acc += value * dim.weight
        if dim.hard_fail_below is not None and value < dim.hard_fail_below:
            hard_dims.append(dim.dimension)
    return acc / total_weight, hard_dims


def _aggregate_dimension_scores(
    case_results: list[CaseResult],
    rubric: list[RubricDimension],
) -> dict[str, float]:
    if not rubric:
        return {}
    totals = {dim.dimension: 0.0 for dim in rubric}
    counts = {dim.dimension: 0 for dim in rubric}
    for case in case_results:
        for dim in rubric:
            if dim.dimension in case.judge_scores:
                totals[dim.dimension] += float(case.judge_scores[dim.dimension])
                counts[dim.dimension] += 1
    return {
        dim: (totals[dim] / counts[dim]) if counts[dim] else 0.0
        for dim in totals
    }


def run_case(
    case: EvalCase,
    *,
    suite: EvalSuite,
    judge: QualitativeJudge,
    workspace: EvalWorkspace,
    toolchain: Optional[dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
    skill_dir: Optional[Path] = None,
    skill_release_hash: Optional[str] = None,
) -> CaseResult:
    """Execute one case through the real executor; never trust suite-authored outputs."""
    if not case_has_execute_block(case):
        if case_has_suite_authored_output(case) or case.suite_authored_output:
            return CaseResult(
                case_id=case.id,
                status=CaseStatus.INVALID_EMBEDDED_OUTPUT,
                observed_output=None,
                reason=(
                    "suite-authored observed_output/fixture_output cannot count as "
                    "execution evidence; declare execute{kind:...} instead"
                ),
                evidence_meta={
                    "executable": False,
                    "suite_authored_output": True,
                    "evidence_source": "suite_authored",
                },
                evidence_source="suite_authored",
            )
        return CaseResult(
            case_id=case.id,
            status=CaseStatus.NOT_EXECUTABLE_PROMPT_ONLY,
            observed_output=None,
            reason="case lacks execute block; not executable for certification",
            evidence_meta={"executable": False, "input_present": bool(case.input)},
            evidence_source="none",
        )

    capture = execute_case(
        case,
        suite=suite,
        workspace=workspace,
        toolchain=toolchain,
        repo_root=repo_root,
        skill_dir=skill_dir,
        skill_release_hash=skill_release_hash,
    )
    if capture.receipt is None:
        return CaseResult(
            case_id=case.id,
            status=CaseStatus.INFRASTRUCTURE_ERROR,
            observed_output=capture.stdout or None,
            reason=capture.error or "executor produced no receipt",
            evidence_meta={
                "executable": True,
                "executor_error": capture.error,
                "evidence_source": "executor_failed",
            },
            evidence_source="executor_failed",
        )

    observed = capture.stdout
    output_path = workspace.write_output(case.id, observed)
    assertion_results = run_assertions(
        observed,
        case.assertions,
        observed_exit_code=capture.exit_code,
        workspace_root=case.workspace_root or workspace.root,
    )
    # Optional golden comparison: suite-authored expected text is a fixture only.
    if case.golden_output is not None and case.raw.get("compare_to_golden"):
        if observed.strip() != case.golden_output.strip():
            assertion_results.append(
                AssertionResult(
                    name="compare_to_golden",
                    passed=False,
                    detail="executed stdout did not match golden fixture",
                    hard_fail=True,
                )
            )

    judge_scores = judge.score(case, observed, suite.rubric, assertion_results)
    case_score, hard_fail_dims = weighted_score(judge_scores, suite.rubric)

    artifact = EvidenceArtifact(
        name=f"{case.id}.stdout",
        kind="executed_stdout",
        path=str(output_path),
        content_hash=workspace.file_hash(output_path),
        metadata={"case_id": case.id, "evidence_source": "executor"},
    )
    receipt_artifact = EvidenceArtifact(
        name=f"{case.id}.receipt",
        kind="execution_receipt",
        path=str(workspace.evidence_dir / f"{case.id}.receipt.json"),
        content_hash=capture.receipt.receipt_hash,
        metadata={"case_id": case.id, "evidence_source": "executor"},
    )
    evidence_meta = {
        "executable": True,
        "evidence_source": "executor",
        "output_path": str(output_path),
        "output_sha256": artifact.content_hash,
        "receipt_hash": capture.receipt.receipt_hash,
        "exit_code": capture.exit_code,
        "tool_calls": [tc.to_dict() for tc in capture.tool_calls],
        "case_score": case_score,
        "assertions_passed": assertions_passed(assertion_results),
        "suite_authored_output_ignored": case.suite_authored_output,
    }
    receipt_dict = capture.receipt.to_dict()

    if capture.error or (capture.exit_code is None and any(tc.timed_out for tc in capture.tool_calls)):
        return CaseResult(
            case_id=case.id,
            status=CaseStatus.INFRASTRUCTURE_ERROR,
            observed_output=observed,
            assertion_results=assertion_results,
            judge_scores=judge_scores,
            case_score=case_score,
            evidence=[artifact, receipt_artifact],
            evidence_meta=evidence_meta,
            reason=capture.error or "executor infrastructure failure",
            execution_receipt=receipt_dict,
            evidence_source="executor",
        )

    if assertions_hard_failed(assertion_results):
        return CaseResult(
            case_id=case.id,
            status=CaseStatus.HARD_FAIL,
            observed_output=observed,
            assertion_results=assertion_results,
            judge_scores=judge_scores,
            case_score=case_score,
            evidence=[artifact, receipt_artifact],
            evidence_meta=evidence_meta,
            reason="hard-fail deterministic assertion",
            execution_receipt=receipt_dict,
            evidence_source="executor",
        )

    if hard_fail_dims:
        return CaseResult(
            case_id=case.id,
            status=CaseStatus.HARD_FAIL,
            observed_output=observed,
            assertion_results=assertion_results,
            judge_scores=judge_scores,
            case_score=case_score,
            evidence=[artifact, receipt_artifact],
            evidence_meta=evidence_meta,
            reason=f"hard_fail_below on dimension(s) {', '.join(hard_fail_dims)!r}",
            execution_receipt=receipt_dict,
            evidence_source="executor",
        )

    if not assertions_passed(assertion_results):
        return CaseResult(
            case_id=case.id,
            status=CaseStatus.FAILED,
            observed_output=observed,
            assertion_results=assertion_results,
            judge_scores=judge_scores,
            case_score=case_score,
            evidence=[artifact, receipt_artifact],
            evidence_meta=evidence_meta,
            reason="deterministic assertions failed",
            execution_receipt=receipt_dict,
            evidence_source="executor",
        )

    return CaseResult(
        case_id=case.id,
        status=CaseStatus.PASSED,
        observed_output=observed,
        assertion_results=assertion_results,
        judge_scores=judge_scores,
        case_score=case_score,
        evidence=[artifact, receipt_artifact],
        evidence_meta=evidence_meta,
        reason="passed executed deterministic checks",
        execution_receipt=receipt_dict,
        evidence_source="executor",
    )


def run_suite(
    suite: EvalSuite,
    *,
    judge: Optional[QualitativeJudge] = None,
    toolchain: Optional[dict[str, Any]] = None,
    workspace: Optional[EvalWorkspace] = None,
    repo_root: Optional[Path] = None,
    skill_dir: Optional[Path] = None,
    skill_release_hash: Optional[str] = None,
) -> SuiteResult:
    """Run all cases in *suite* through the real executor and aggregate results."""
    active_judge: QualitativeJudge = judge or IndependentDeterministicJudge()
    owns_workspace = workspace is None
    ws = workspace or EvalWorkspace()
    case_results: list[CaseResult] = []
    reasons: list[str] = []
    evidence: list[EvidenceArtifact] = []
    execution_receipts: list[dict[str, Any]] = []
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[3]

    try:
        for case in suite.cases:
            result = run_case(
                case,
                suite=suite,
                judge=active_judge,
                workspace=ws,
                toolchain=toolchain,
                repo_root=root,
                skill_dir=skill_dir,
                skill_release_hash=skill_release_hash,
            )
            case_results.append(result)
            evidence.extend(result.evidence)
            if result.execution_receipt:
                execution_receipts.append(result.execution_receipt)
            if result.status == CaseStatus.NOT_EXECUTABLE_PROMPT_ONLY:
                reasons.append(f"{case.id}: not_executable_prompt_only")
            if result.status == CaseStatus.INVALID_EMBEDDED_OUTPUT:
                reasons.append(f"{case.id}: invalid_embedded_output")

        dimension_scores = _aggregate_dimension_scores(case_results, suite.rubric)
        weighted, hard_dims = weighted_score(dimension_scores, suite.rubric)

        scored = [c for c in case_results if c.case_score is not None]
        if scored:
            weighted = sum(float(c.case_score or 0.0) for c in scored) / len(scored)

        has_blocked = any(
            c.status
            in {
                CaseStatus.NOT_EXECUTABLE_PROMPT_ONLY,
                CaseStatus.INVALID_EMBEDDED_OUTPUT,
            }
            for c in case_results
        )
        any_failed = any(
            c.status
            in {
                CaseStatus.FAILED,
                CaseStatus.HARD_FAIL,
                CaseStatus.INFRASTRUCTURE_ERROR,
            }
            for c in case_results
        )
        all_executable_passed = (
            bool(case_results)
            and not has_blocked
            and not any_failed
            and all(c.status == CaseStatus.PASSED for c in case_results)
            and all(c.evidence_source == "executor" for c in case_results)
            and all(c.execution_receipt for c in case_results)
        )
        passed = (
            all_executable_passed
            and weighted >= suite.pass_threshold
            and not hard_dims
        )
        certifiable = passed and not has_blocked

        if has_blocked:
            reasons.append(
                "suite contains non-executable or suite-authored-output cases; cannot certify"
            )
            certifiable = False
        if hard_dims:
            reasons.append(f"hard_fail_below dimensions: {', '.join(hard_dims)}")
            certifiable = False
        if not case_results:
            reasons.append("suite has no cases")
            certifiable = False
        if any(not c.execution_receipt for c in case_results):
            reasons.append("missing immutable execution receipt(s)")
            certifiable = False

        receipt = ws.receipt()
        return SuiteResult(
            skill_id=suite.skill_id,
            suite_id=suite.suite_id,
            suite_version=suite.suite_version,
            suite_hash=suite.suite_hash,
            case_results=case_results,
            judge_kind=getattr(active_judge, "kind", type(active_judge).__name__),
            toolchain=dict(toolchain or {}),
            weighted_score=weighted,
            dimension_scores=dimension_scores,
            hard_fail_dimensions=hard_dims,
            passed=passed,
            certifiable=certifiable,
            reasons=reasons,
            workspace_receipt=receipt,
            evidence=evidence,
            execution_receipts=execution_receipts,
        )
    finally:
        if owns_workspace:
            ws.cleanup()


# Backward-compatible alias.
RunResult = SuiteResult
