#!/usr/bin/env python3
"""
Cross-skill analytics for LiNKskills libraries.

Scans execution_ledger.jsonl and skill folders to produce a health report with
failure/HITL rates and refinement recommendations.
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_CONFIG = {
    "logging": {
        "ledger_path": "execution_ledger.jsonl",
    },
    "engine": {
        "tier_order": ["fast", "balanced", "high"],
        "environment": {
            "reasoning_tier": "high",
            "context_window": 200000,
        },
    },
}


def strip_yaml_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for idx, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return line[:idx].rstrip()
    return line.rstrip()


def parse_yaml_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip('"').strip("'") for part in inner.split(",")]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if re.match(r"^-?\d+$", value):
        return int(value)
    if re.match(r"^-?\d+\.\d+$", value):
        return float(value)
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(-1, root)]

    for raw in text.splitlines():
        line = strip_yaml_comment(raw)
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.lstrip(" ")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(-1, root)]
        parent = stack[-1][1]
        if value == "":
            parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            parent[key] = parse_yaml_scalar(value)
    return root


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(root: Path) -> Dict[str, Any]:
    config_path = root / "global_config.yaml"
    if not config_path.exists():
        return DEFAULT_CONFIG
    parsed = parse_simple_yaml(config_path.read_text(encoding="utf-8"))
    return deep_merge(DEFAULT_CONFIG, parsed)


def parse_timestamp(value: str) -> Optional[datetime]:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def extract_frontmatter(content: str) -> Dict[str, Any]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return {}
    frontmatter_text = "\n".join(lines[1:end_idx])
    return parse_simple_yaml(frontmatter_text)


def normalize_tier_order(raw_tier_order: Any) -> List[str]:
    default = ["fast", "balanced", "high"]
    if not isinstance(raw_tier_order, list):
        return default
    cleaned = [tier for tier in raw_tier_order if isinstance(tier, str) and tier]
    return cleaned or default


def read_skill_engine_profile(skill_path: Path) -> Dict[str, Any]:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return {}
    frontmatter = extract_frontmatter(skill_md.read_text(encoding="utf-8"))
    engine = frontmatter.get("engine")
    if isinstance(engine, dict):
        return engine
    return {}


def evaluate_engine_floor(
    engine_profile: Dict[str, Any],
    engine_policy: Dict[str, Any],
) -> Optional[bool]:
    if not engine_profile:
        return None

    tier_order = normalize_tier_order(engine_policy.get("tier_order"))
    rank = {tier: idx for idx, tier in enumerate(tier_order)}

    min_tier = engine_profile.get("min_reasoning_tier")
    context_required = engine_profile.get("context_required")
    env = engine_policy.get("environment", {})
    env_tier = env.get("reasoning_tier")
    env_context = env.get("context_window")

    if not isinstance(min_tier, str) or min_tier not in rank:
        return None
    if not isinstance(env_tier, str) or env_tier not in rank:
        return None
    if not isinstance(context_required, int) or not isinstance(env_context, int):
        return None

    tier_ok = rank[min_tier] <= rank[env_tier]
    context_ok = context_required <= env_context
    return tier_ok and context_ok


def discover_skills(root: Path) -> List[str]:
    skills_root = root / "skills"
    skills: List[str] = []
    if not skills_root.exists():
        return skills
    for path in skills_root.iterdir():
        if path.is_dir() and (path / "SKILL.md").exists():
            skills.append(path.name)
    return sorted(skills)


def count_old_pattern_entries(skill_path: Path) -> int:
    old_patterns = skill_path / "references" / "old-patterns.md"
    if not old_patterns.exists():
        return 0
    count = 0
    for line in old_patterns.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- **") and "[Pattern Name]" not in stripped and "[Failure ID]" not in stripped:
            count += 1
    return count


def load_ledger_entries(ledger_file: Path) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    if not ledger_file.exists():
        return entries
    with ledger_file.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                entries.append(payload)
    return entries


def is_failure_status(status: str) -> bool:
    normalized = status.upper()
    return "FAIL" in normalized or "ERROR" in normalized


def generate_report(
    root: Path,
    ledger_path: Path,
    failure_threshold: float,
    hitl_threshold: float,
    engine_policy: Dict[str, Any],
) -> Dict[str, Any]:
    skills = discover_skills(root)
    entries = load_ledger_entries(ledger_path)

    per_skill: Dict[str, Dict[str, Any]] = {
        skill: {
            "skill": skill,
            "total_runs": 0,
            "completed": 0,
            "failed": 0,
            "pending_approval": 0,
            "latest_timestamp": None,
            "old_pattern_entries": count_old_pattern_entries(root / "skills" / skill),
            "changelog_present": (root / "skills" / skill / "references" / "changelog.md").exists(),
            "engine_profile": read_skill_engine_profile(root / "skills" / skill),
            "flags": [],
        }
        for skill in skills
    }

    for entry in entries:
        skill = entry.get("skill")
        if not isinstance(skill, str):
            continue
        if skill not in per_skill:
            per_skill[skill] = {
                "skill": skill,
                "total_runs": 0,
                "completed": 0,
                "failed": 0,
                "pending_approval": 0,
                "latest_timestamp": None,
                "old_pattern_entries": 0,
                "changelog_present": False,
                "flags": ["ledger_skill_not_found_locally"],
            }

        stat = per_skill[skill]
        status = str(entry.get("status", "UNKNOWN"))
        stat["total_runs"] += 1
        if status == "COMPLETED":
            stat["completed"] += 1
        if status == "PENDING_APPROVAL":
            stat["pending_approval"] += 1
        if is_failure_status(status):
            stat["failed"] += 1

        ts_raw = entry.get("timestamp")
        if isinstance(ts_raw, str):
            parsed = parse_timestamp(ts_raw)
            if parsed is not None:
                current = stat["latest_timestamp"]
                if current is None or parsed > current:
                    stat["latest_timestamp"] = parsed

    report_skills: List[Dict[str, Any]] = []
    high_failure = 0
    high_hitl = 0
    for skill_name in sorted(per_skill.keys()):
        stat = per_skill[skill_name]
        total = stat["total_runs"]
        failure_rate = (stat["failed"] / total) if total else 0.0
        hitl_rate = (stat["pending_approval"] / total) if total else 0.0

        flags = list(stat["flags"])
        if total == 0:
            flags.append("no_execution_data")
        if total and failure_rate >= failure_threshold:
            flags.append("high_failure_rate")
            high_failure += 1
        if total and hitl_rate >= hitl_threshold:
            flags.append("high_hitl_pause_rate")
            high_hitl += 1
        if not stat["changelog_present"]:
            flags.append("missing_changelog")

        engine_profile = stat.get("engine_profile", {})
        floor_met = evaluate_engine_floor(engine_profile, engine_policy)
        if floor_met is False:
            flags.append("engine_floor_unmet")
        if floor_met is None:
            flags.append("engine_floor_unknown")

        latest = stat["latest_timestamp"]
        report_skills.append(
            {
                "skill": skill_name,
                "total_runs": total,
                "completed": stat["completed"],
                "failed": stat["failed"],
                "pending_approval": stat["pending_approval"],
                "failure_rate": round(failure_rate, 4),
                "hitl_pause_rate": round(hitl_rate, 4),
                "latest_timestamp": latest.isoformat().replace("+00:00", "Z") if latest else None,
                "old_pattern_entries": stat["old_pattern_entries"],
                "changelog_present": stat["changelog_present"],
                "engine_min_reasoning_tier": engine_profile.get("min_reasoning_tier"),
                "engine_context_required": engine_profile.get("context_required"),
                "engine_floor_met": floor_met,
                "flags": flags,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ledger_path": str(ledger_path),
        "thresholds": {
            "failure_rate": failure_threshold,
            "hitl_pause_rate": hitl_threshold,
        },
        "engine_environment": engine_policy.get("environment", {}),
        "summary": {
            "skills_evaluated": len(report_skills),
            "skills_with_high_failure_rate": high_failure,
            "skills_with_high_hitl_pause_rate": high_hitl,
        },
        "skills": report_skills,
    }


def render_text(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"Global Skill Health Report ({report['generated_at']})")
    lines.append(f"Ledger: {report['ledger_path']}")
    lines.append(
        "Thresholds: "
        f"failure_rate>={report['thresholds']['failure_rate']}, "
        f"hitl_pause_rate>={report['thresholds']['hitl_pause_rate']}"
    )
    lines.append(f"Engine environment: {report.get('engine_environment', {})}")
    lines.append("")

    for skill in report["skills"]:
        lines.append(
            f"- {skill['skill']}: runs={skill['total_runs']} completed={skill['completed']} "
            f"failed={skill['failed']} pending={skill['pending_approval']} "
            f"failure_rate={skill['failure_rate']:.2f} hitl_rate={skill['hitl_pause_rate']:.2f}"
        )
        lines.append(
            "  engine: "
            f"tier={skill.get('engine_min_reasoning_tier')} "
            f"context={skill.get('engine_context_required')} "
            f"floor_met={skill.get('engine_floor_met')}"
        )
        if skill["flags"]:
            lines.append(f"  flags: {', '.join(skill['flags'])}")
        if skill["latest_timestamp"]:
            lines.append(f"  latest: {skill['latest_timestamp']}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate cross-skill health analytics")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--ledger",
        default=None,
        help="Ledger path override (defaults to global_config.yaml logging.ledger_path)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument("--output", default=None, help="Optional output file path")
    parser.add_argument("--failure-threshold", type=float, default=0.20)
    parser.add_argument("--hitl-threshold", type=float, default=0.30)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config = load_config(root)
    ledger_value = args.ledger or config.get("logging", {}).get("ledger_path", "execution_ledger.jsonl")
    ledger_path = (root / ledger_value).resolve() if not Path(ledger_value).is_absolute() else Path(ledger_value)

    report = generate_report(
        root=root,
        ledger_path=ledger_path,
        failure_threshold=args.failure_threshold,
        hitl_threshold=args.hitl_threshold,
        engine_policy=config.get("engine", {}) if isinstance(config.get("engine"), dict) else {},
    )
    output = json.dumps(report, indent=2) if args.format == "json" else render_text(report)

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
