#!/usr/bin/env python3
"""Prepare the governed initial-skill canary admission artifacts.

This script does not activate a consumer, grant tool authority, update a live
pointer, or claim stable qualification. It turns the reviewed source inventory
into deterministic, fail-closed canary admission metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECIDED_AT = "2026-08-31T12:00:00Z"
AUDITOR = "linkskills-issue-299-initial-canary-audit"

COLLECTIONS = {
    "awesome-design": ("awesome-design-presets", ["cursor-macos", "codex-macos"]),
    "emil-design": ("emil-design-engineering", ["cursor-macos", "codex-macos"]),
    "google-workspace": ("google-workspace-operations", ["gws-consumer"]),
    "hybrid-development": ("hybrid-development-methods", ["cursor-macos", "codex-macos"]),
    "impeccable": ("impeccable-design-system", ["cursor-macos", "codex-macos"]),
    "taste-design": ("taste-design-exploration", ["cursor-macos", "codex-macos"]),
}

EXCEPTIONS = {
    "taste-gpt-tasteskill": (
        "needs_correction",
        ["rigid_universal_design_rules", "accessibility_and_performance_conflict"],
    ),
    "taste-output-skill": (
        "needs_correction",
        ["cross_cutting_output_override", "outside_design_family_boundary"],
    ),
    "taste-taste-skill-v1": (
        "superseded",
        ["backward_compatibility_only", "superseded_by_taste_taste_skill"],
    ),
}

CONSUMERS = {
    "ide-development": {
        "runtime_profiles": ["cursor-macos", "codex-macos"],
        "collections": list(COLLECTIONS.keys() - {"google-workspace"}),
        "exclude": set(),
        "purpose": "software delivery plus website and application design",
    },
    "linkdeveloper": {
        "runtime_profiles": ["cursor-macos", "codex-macos"],
        "collections": list(COLLECTIONS.keys() - {"google-workspace"}),
        "exclude": set(),
        "purpose": "web, Expo, Swift, Apple-platform and general application delivery",
    },
    "linksites": {
        "runtime_profiles": ["cursor-macos", "codex-macos"],
        "collections": list(COLLECTIONS.keys() - {"google-workspace"}),
        "exclude": {
            "taste-imagegen-frontend-mobile",
            "emil-apple-design",
            "emil-animate-expo",
            "emil-write-swift",
        },
        "purpose": "website design, implementation, review and polish",
    },
    "google-workspace": {
        "runtime_profiles": ["gws-consumer"],
        "collections": ["google-workspace"],
        "exclude": set(),
        "purpose": "Google Workspace operations selected by an authorized consumer",
    },
}


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def digest_json(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return "sha256:" + hashlib.sha256(body).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class Writer:
    def __init__(self, check: bool) -> None:
        self.check = check
        self.changed: list[str] = []

    def json(self, path: Path, value: Any) -> None:
        self.bytes(path, canonical_bytes(value))

    def text(self, path: Path, value: str) -> None:
        self.bytes(path, value.encode())

    def bytes(self, path: Path, value: bytes) -> None:
        current = path.read_bytes() if path.is_file() else None
        if current == value:
            return
        self.changed.append(path.relative_to(ROOT).as_posix())
        if not self.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)


def classification(skill_id: str) -> tuple[str, list[str]]:
    return EXCEPTIONS.get(
        skill_id,
        (
            "approved_internal_canary",
            [
                "source_integrity_verified",
                "license_reviewed_compatible",
                "required_structure_present",
                "no_exact_duplicate",
                "family_scope_accepted",
            ],
        ),
    )


def update_collection_records(
    writer: Writer,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    audit_members: list[dict[str, Any]] = []
    member_index: dict[str, dict[str, Any]] = {}
    for collection_id, (adapter_id, profiles) in sorted(COLLECTIONS.items()):
        collection_root = ROOT / "collections" / collection_id
        manifest_path = collection_root / "collection-manifest.json"
        manifest = load(manifest_path)
        manifest["lifecycle_state"] = "eval_pending"
        unsigned = {key: value for key, value in manifest.items() if key != "manifest_digest"}
        manifest["manifest_digest"] = digest_json(unsigned)
        writer.json(manifest_path, manifest)

        for member in sorted(manifest["members"], key=lambda item: item["skill_id"]):
            skill_id = member["skill_id"]
            decision, reasons = classification(skill_id)
            approved = decision == "approved_internal_canary"
            release_path = collection_root / "releases" / f"{skill_id}.json"
            release = load(release_path)
            release.pop("supersedes_release_id", None)
            if approved:
                release["channel"] = "canary"
                release["lifecycle_state"] = "eval_pending"
                release["execution_profiles"] = profiles
                release["notes"] = (
                    "Approved source candidate for internal canary use; stable qualification, "
                    "consumer activation, tool authority, and live publication are not claimed."
                )
            elif decision == "superseded":
                release["channel"] = "development"
                release["lifecycle_state"] = "superseded"
                release["execution_profiles"] = profiles
                release["notes"] = "Preserved for backward compatibility; blocked because the current Taste route replaces it."
            else:
                release["channel"] = "development"
                release["lifecycle_state"] = "unqualified"
                release["execution_profiles"] = profiles
                release["notes"] = "Preserved source; blocked from canary routing pending correction and re-audit."
            writer.json(release_path, release)

            eligibility_path = collection_root / "eligibility" / f"{skill_id}-ineligible.json"
            eligibility = load(eligibility_path)
            eligibility["evaluated_at"] = DECIDED_AT
            eligibility["decision"] = "ineligible"
            eligibility["platform_technical_eligibility"] = {
                "status": approved,
                "evidence_ref": f"opaque:evidence:issue-299-{skill_id}-source-audit",
                "evaluated_by": AUDITOR,
            }
            eligibility["skills_release_selectability"] = {
                "status": False,
                "evidence_ref": f"opaque:evidence:issue-299-{skill_id}-not-selectable",
                "evaluated_by": AUDITOR,
            }
            eligibility["consumer_profile_activation"] = {
                "status": False,
                "evidence_ref": f"opaque:evidence:issue-299-{skill_id}-consumer-inactive",
                "evaluated_by": AUDITOR,
            }
            eligibility["consumer_tool_authority"] = {
                "status": False,
                "evidence_ref": f"opaque:evidence:issue-299-{skill_id}-tool-unauthorized",
                "evaluated_by": AUDITOR,
            }
            denials = ["release_not_selectable", "profile_not_activated", "tool_not_authorized"]
            if not approved:
                denials.append("superseded" if decision == "superseded" else "unqualified")
                denials.insert(0, "missing_platform_evidence")
            eligibility["denial_reasons"] = denials
            writer.json(eligibility_path, eligibility)

            record = {
                "adapter_skill_id": adapter_id,
                "collection_id": collection_id,
                "decision": decision,
                "ordinary_selectable": False,
                "rationale_codes": reasons,
                "release_id": member["release_id"],
                "runtime_profiles": profiles,
                "skill_id": skill_id,
                "stable_qualified": False,
            }
            audit_members.append(record)
            member_index[skill_id] = record
    return audit_members, member_index


def parse_description(skill_path: Path) -> str:
    text = skill_path.read_text(encoding="utf-8")
    match = re.search(r"(?m)^description:\s*[\"']?(.*?)[\"']?\s*$", text)
    return match.group(1).strip() if match else skill_path.parent.name.replace("-", " ")


def google_routing() -> dict[str, Any]:
    manifest = load(ROOT / "collections/google-workspace/collection-manifest.json")
    routes = []
    for member in sorted(manifest["members"], key=lambda item: item["skill_id"]):
        skill_id = member["skill_id"]
        phrase = skill_id.removeprefix("gws-").replace("-", " ")
        routes.append(
            {
                "description": parse_description(ROOT / "vendor-skills/google-workspace" / skill_id / "SKILL.md"),
                "keywords": [phrase, skill_id],
                "route_id": skill_id,
                "source_entrypoint": f"vendor-skills/google-workspace/{skill_id}/SKILL.md",
            }
        )
    return {
        "routes": routes,
        "schema_version": "0.1",
        "selection_rule": "Prefer an explicit route id; fail closed on no match, ambiguity, or blocked admission.",
        "skill_id": "google-workspace-operations",
        "source_collection": "google-workspace",
    }


HELPER = '''#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--route")
    parser.add_argument("--route-id")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "references" / "routing.json").read_text())
    admission_doc = json.loads((root / "references" / "admission.json").read_text())
    admission = {item["route_id"]: item for item in admission_doc["members"]}
    routes = {item["route_id"]: item for item in data["routes"]}
    if args.list:
        print(json.dumps({"routes": [{"route_id": route_id, "admission_state": admission[route_id]["admission_state"], "routing_allowed": admission[route_id]["routing_allowed"]} for route_id in sorted(routes)]}, sort_keys=True))
        return 0
    if bool(args.route) == bool(args.route_id):
        parser.error("exactly one of --list, --route, or --route-id is required")
    if args.route_id:
        route = routes.get(args.route_id)
        if route is None:
            result = {"status": "NOT_APPLICABLE", "selected_route": None, "source_entrypoint": None, "release_id": None, "admission_state": None, "ordinary_selectable": False, "alternatives": [], "reason": "unknown route id"}
        else:
            scored = [(1, route["route_id"], route["source_entrypoint"])]
    else:
        task = args.route.casefold()
        scored = []
        for route in data["routes"]:
            score = sum(1 for word in route["keywords"] if word.casefold() in task)
            if score:
                scored.append((score, route["route_id"], route["source_entrypoint"]))
        scored.sort(key=lambda item: (-item[0], item[1]))
    if 'result' not in locals():
        if not scored:
            result = {"status": "NOT_APPLICABLE", "selected_route": None, "source_entrypoint": None, "release_id": None, "admission_state": None, "ordinary_selectable": False, "alternatives": [], "reason": "no route matched"}
        elif len(scored) > 1 and scored[0][0] == scored[1][0]:
            result = {"status": "AMBIGUOUS", "selected_route": None, "source_entrypoint": None, "release_id": None, "admission_state": None, "ordinary_selectable": False, "alternatives": [item[1] for item in scored if item[0] == scored[0][0]][:2], "reason": "top routes tied"}
        else:
            selected = scored[0]
            gate = admission[selected[1]]
            if not gate["routing_allowed"]:
                result = {"status": "NOT_ELIGIBLE", "selected_route": selected[1], "source_entrypoint": None, "release_id": gate["release_id"], "admission_state": gate["admission_state"], "ordinary_selectable": False, "alternatives": [], "reason": "member is not approved for internal canary routing"}
            else:
                result = {"status": "SELECTED", "selected_route": selected[1], "source_entrypoint": selected[2], "release_id": gate["release_id"], "admission_state": gate["admission_state"], "ordinary_selectable": False, "alternatives": [], "reason": "one approved internal-canary route matched"}
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'''


def update_adapters(writer: Writer) -> None:
    writer.json(ROOT / "skills/google-workspace-operations/references/routing.json", google_routing())
    for _, (adapter_id, _) in sorted(COLLECTIONS.items()):
        routing_path = ROOT / "skills" / adapter_id / "references/routing.json"
        routing = load(routing_path)
        if adapter_id == "awesome-design-presets":
            for route in routing["routes"]:
                if route["route_id"] == "awesome-impeccable":
                    route["keywords"] = ["burnt orange editorial preset", "orange editorial style"]
            writer.json(routing_path, routing)
        collection_id = routing["source_collection"]
        collection = load(ROOT / "collections" / collection_id / "collection-manifest.json")
        releases = {item["skill_id"]: item["release_id"] for item in collection["members"]}
        routed_admission = []
        for route in routing["routes"]:
            source_member = Path(route["source_entrypoint"]).parts[2]
            decision, _ = classification(source_member)
            routed_admission.append(
                {
                    "admission_state": decision,
                    "ordinary_selectable": False,
                    "release_id": releases[source_member],
                    "route_id": route["route_id"],
                    "routing_allowed": decision == "approved_internal_canary",
                    "source_member_id": source_member,
                }
            )
        writer.json(
            ROOT / "skills" / adapter_id / "references" / "admission.json",
            {
                "adapter_skill_id": adapter_id,
                "collection_id": collection_id,
                "decided_at": DECIDED_AT,
                "members": routed_admission,
                "schema_version": "0.1",
            },
        )
        writer.text(ROOT / "skills" / adapter_id / "scripts/helper_tool.py", HELPER)
        schemas_path = ROOT / "skills" / adapter_id / "references/schemas.json"
        if schemas_path.is_file():
            schemas = load(schemas_path)
            output = schemas["definitions"]["output"]
            if "NOT_ELIGIBLE" not in output["properties"]["status"]["enum"]:
                output["properties"]["status"]["enum"].append("NOT_ELIGIBLE")
            output["properties"].update(
                {
                    "admission_state": {"type": ["string", "null"]},
                    "ordinary_selectable": {"type": "boolean"},
                    "release_id": {"type": ["string", "null"]},
                }
            )
            for field in ("admission_state", "ordinary_selectable", "release_id"):
                if field not in output["required"]:
                    output["required"].append(field)
            writer.json(schemas_path, schemas)


def build_activation_manifests(
    writer: Writer,
    members: list[dict[str, Any]],
) -> None:
    for consumer_id, policy in sorted(CONSUMERS.items()):
        permitted = [
            item
            for item in members
            if item["decision"] == "approved_internal_canary"
            and item["collection_id"] in policy["collections"]
            and item["skill_id"] not in policy["exclude"]
        ]
        adapters = sorted({item["adapter_skill_id"] for item in permitted})
        writer.json(
            ROOT / "configs/consumer-activation" / f"{consumer_id}-internal-canary.json",
            {
                "activation": {"activation_owner": "consumer", "enabled": False},
                "adapter_skill_ids": adapters,
                "consumer_id": consumer_id,
                "consumer_apply_required": True,
                "generated_from": "opaque:evidence:issue-299-initial-skill-seed-classification",
                "live_apply": False,
                "permitted_release_ids": sorted(item["release_id"] for item in permitted),
                "purpose": policy["purpose"],
                "runtime_profiles": policy["runtime_profiles"],
                "schema_version": "0.1",
                "stable_qualification_claimed": False,
            },
        )


def build_audit(writer: Writer, members: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for item in members:
        counts[item["decision"]] = counts.get(item["decision"], 0) + 1
    audit: dict[str, Any] = {
        "criteria": [
            "source_integrity",
            "license_compatibility",
            "required_structure",
            "exact_duplicate_detection",
            "family_scope_and_overlap",
            "instruction_safety",
            "runtime_profile_compatibility",
        ],
        "decided_at": DECIDED_AT,
        "decision_authority": "Principal approval for initial internal canary admission",
        "kind": "initial-skill-seed-canary-admission",
        "members": sorted(members, key=lambda item: (item["collection_id"], item["skill_id"])),
        "publication_boundary": {
            "consumer_activation": False,
            "live_provider_publish": False,
            "ordinary_selectability": False,
            "stable_qualification": False,
        },
        "schema_version": "0.1",
        "summary": {"counts": counts, "total": len(members)},
    }
    audit["classification_digest"] = digest_json(audit)
    writer.json(ROOT / "evidence/initial-skill-seed/member-classification.json", audit)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    writer = Writer(args.check)
    members, _ = update_collection_records(writer)
    update_adapters(writer)
    build_activation_manifests(writer, members)
    build_audit(writer, members)
    if writer.changed:
        if args.check:
            print("generated artifacts are stale:")
            print("\n".join(writer.changed))
            return 1
        print(f"updated {len(writer.changed)} files")
    else:
        print("generated artifacts are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
